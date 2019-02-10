#!/bin/bash

clear

#-----------------------------
# UPDATE THESE VARIABLES
#-----------------------------
STACK_NAME=iot-collar
S3_BUCKET=werberm-sandbox
CERT_C='US'
CERT_ST='New York'
CERT_L='New York'
CERT_O='Mathew Werber'
CERT_OU='IoT'
ROOT_CERT_CN='iot.matwerber.info'
DEVICE_CERT_CN='mydevice123'
THING_TYPE_NAME="dog_collar"

#-----------------------------
# DO NOT CHANGE THESE VARS
#-----------------------------
IOT_REGISTRATION_CODE=''
JITP_ROLE_ARN=''
BUILD_DIR=build
ROOT_CERT_DIR="$BUILD_DIR/root-cert"
DEVICE_CERT_DIR="$BUILD_DIR/device-cert"
AWS_IOT_CERT_DIR="$BUILD_DIR/aws-iot-cert"

#-----------------------------
# Create build output folder
mkdir -p $BUILD_DIR
mkdir -p $ROOT_CERT_DIR
mkdir -p $DEVICE_CERT_DIR
mkdir -p $AWS_IOT_CERT_DIR

update_cloudformation() {
    # Deploy CloudFormation
    aws cloudformation deploy               \
    --template-file cloudformation.yaml     \
    --stack-name $STACK_NAME                \
    --s3-bucket $S3_BUCKET                  \
    --capabilities CAPABILITY_NAMED_IAM

    # Get IoT Registration Code needed for IoT Verification Certificate
    IOT_REGISTRATION_CODE=$(aws iot get-registration-code)

    # Get JITP IAM Role ARN from CloudFormation stack
    JITP_ROLE_ARN=$(aws cloudformation describe-stacks      \
        --stack-name $STACK_NAME                            \
        --query 'Stacks[0].Outputs[?OutputKey==`JITPRoleArn`].OutputValue'  \
        --output text
    )
}

create_provisioning_template() {  

    # Create an IoT JITP provisioning template using the proper IAM Role ARN created above
    echo 'Creating IoT JITP provisioning template...'
    PROVISIONING_TEMPLATE=$(<./templates/provisioning-template.json)

    # Add in role ARN
    PROVISIONING_TEMPLATE=${PROVISIONING_TEMPLATE//<JITP_ROLE_ARN>/$JITP_ROLE_ARN} 

    # Add in thing name
    PROVISIONING_TEMPLATE=${PROVISIONING_TEMPLATE//<THING_TYPE_NAME>/$THING_TYPE_NAME} 

    echo $PROVISIONING_TEMPLATE > $ROOT_CERT_DIR/provisioning-template.json

}

create_and_register_iot_ca_cert() {

    FILE="$ROOT_CERT_DIR/aws_ca_cert_arn.txt"

    if [ -f $FILE ]; then
        echo "CA Cert already registered with IoT, skipping cert creation & registration..."
    else
        # Generate Root CA Key
        echo 'Creating Root CA key...'
        openssl genrsa -out $ROOT_CERT_DIR/rootCA.key 2048

        # Create Root CA Certificate from Root CA Key
        echo 'Creating Root CA Certificate...'
        openssl req                     \
            -x509                       \
            -new                        \
            -nodes                      \
            -sha256                     \
            -days 1024                  \
            -key $ROOT_CERT_DIR/rootCA.key     \
            -out $ROOT_CERT_DIR/rootCA.pem     \
            -subj "/C=$CERT_C/ST=$CERT_ST/L=$CERT_L/O=$CERT_O/OU=$CERT_OU/CN=$ROOT_CERT_CN/"

        # Generate an IoT Verification Key
        echo 'Create IoT verification key...'
        openssl genrsa -out $ROOT_CERT_DIR/verificationCert.key 2048

        # Our verification cert's CN must be the IoT registration code...
        VERIFICATION_CERT_CN=$IOT_REGISTRATION_CODE

        # Generate our verification certificate signing request (CSR)
        echo 'Create verification CSR...'
        openssl req                                     \
            -new                                        \
            -key $ROOT_CERT_DIR/verificationCert.key             \
            -out $ROOT_CERT_DIR/verificationCert.csr             \
            -subj "/C=$CERT_C/ST=$CERT_ST/L=$CERT_L/O=$CERT_O/OU=$CERT_OU/CN=$VERIFICATION_CERT_CN/"

        # Generate verification certificate
        echo 'Create verification certificate...'
        openssl x509                                    \
            -req                                        \
            -CAcreateserial                             \
            -days 500                                   \
            -sha256                                     \
            -CA    $ROOT_CERT_DIR/rootCA.pem                     \
            -CAkey $ROOT_CERT_DIR/rootCA.key                     \
            -in    $ROOT_CERT_DIR/verificationCert.csr           \
            -out   $ROOT_CERT_DIR/verificationCert.pem

        # Register our Root CA Certificate with AWS IoT Core; use verification cert to prove we own the root CA cert
        echo 'Register CA certificate with AWS IoT...'
        AWS_CA_CERT_ARN=$(
        aws iot register-ca-certificate                                     \
            --ca-certificate file://$ROOT_CERT_DIR/rootCA.pem                        \
            --verification-cert file://$ROOT_CERT_DIR/verificationCert.pem           \
            --set-as-active                                                 \
            --allow-auto-registration                                       \
            --registration-config file://$ROOT_CERT_DIR/provisioning-template.json
        )

        # Store cert ARN in file for later reference
        echo $AWS_CA_CERT_ARN > $ROOT_CERT_DIR/aws_ca_cert_arn.txt

        # Echo results
        echo "CA Cert registered with AWS: $AWS_CA_CERT_ARN"
    fi
}

create_device_cert() {

    FILE="$DEVICE_CERT_DIR/deviceCert.crt"

    if [ -f $FILE ]; then
        echo "Device cert already exists, skipping cert creation..."
    else
        # Generate device key
        openssl genrsa                      \
            -out $DEVICE_CERT_DIR/deviceCert.key \
            2048

        # Generate device CSR
        openssl req                             \
            -new                                \
            -key $DEVICE_CERT_DIR/deviceCert.key     \
            -out $DEVICE_CERT_DIR/deviceCert.csr     \
            -subj "/C=$CERT_C/ST=$CERT_ST/L=$CERT_L/O=$CERT_O/OU=$CERT_OU/CN=$DEVICE_CERT_CN/"

        # Generate a device certificate
        openssl x509                            \
            -req                                \
            -CAcreateserial                     \
            -days 365                           \
            -sha256                             \
            -CA $ROOT_CERT_DIR/rootCA.pem         \
            -CAkey $ROOT_CERT_DIR/rootCA.key      \
            -in $DEVICE_CERT_DIR/deviceCert.csr      \
            -out $DEVICE_CERT_DIR/deviceCert.crt

        # Create file containing both device cert and root CA cert
        cat $DEVICE_CERT_DIR/deviceCert.crt $ROOT_CERT_DIR/rootCA.pem > $DEVICE_CERT_DIR/deviceCertAndCACert.crt

    fi       
}

download_iot_root_cert() {

    curl                                \
        --output $AWS_IOT_CERT_DIR/root.cert  \
        https://www.symantec.com/content/en/us/enterprise/verisign/roots/VeriSign-Class%203-Public-Primary-Certification-Authority-G5.pem
}

publish_device_cert_to_aws_iot() {
    
    echo 'Publishing device cert to AWS IoT...'
    IOT_ENDPOINT=$(aws iot describe-endpoint)

    # Register device cert with AWS IoT
    mosquitto_pub                                               \
        --cafile $AWS_IOT_CERT_DIR/root.cert                    \
        --cert $DEVICE_CERT_DIR/deviceCertAndCACert.crt         \
        --key $DEVICE_CERT_DIR/deviceCert.key                   \
        -h $IOT_ENDPOINT                                        \
        -p 8883                                                 \
        -q 1                                                    \
        -t foo/bar                                              \
        -I anyclientID                                          \
        --tls-version tlsv1.2                                   \
        -m "Hello"                                              \
        -d                                      

}

create_aws_iot_thing_type() {

    echo "Creating AWS IoT thing type $THING_TYPE_NAME"

    aws iot create-thing-type   \
        --thing-type-name "dog_collar"

}

main() {
    create_aws_iot_thing_type
    update_cloudformation
    create_provisioning_template
    create_and_register_iot_ca_cert
    create_device_cert
    download_iot_root_cert
    publish_device_cert_to_aws_iot
}

main