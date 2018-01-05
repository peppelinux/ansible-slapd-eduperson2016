````
# Create the directory structure. The index.txt and serial files act as a flat file database to keep track of signed certificates.
mkdir CA
cd CA
mkdir certs crl newcerts private
chmod 700 private
touch index.txt
echo 1000 > serial

# create and customize configuration file
cp /etc/ssl/openssl.cnf openssl.cnf
#nano openssl.cnf

# create root key
openssl genrsa -aes256 -out private/ca.key.pem 4096
chmod 400 private/ca.key.pem

# create the root certificate
openssl req -config openssl.cnf \
      -key private/ca.key.pem \
      -new -x509 -days 7300 -sha256 -extensions v3_ca \
      -out certs/ca.cert.pem
chmod 444 certs/ca.cert.pem

# Verify the root certificate
openssl x509 -noout -text -in certs/ca.cert.pem

# Create Intermediate pair
# The purpose of using an intermediate CA is primarily for security. 
# The root key can be kept offline and used as infrequently as possible. 
# If the intermediate key is compromised, the root CA can revoke the
# intermediate certificate and create a new intermediate cryptographic pair.
mkdir intermediate
cd intermediate
mkdir certs crl csr newcerts private
chmod 700 private
touch index.txt
echo 1000 > serial
echo 1000 > crlnumber

````
