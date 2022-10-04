BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "mined_transactions" (
	"block_index"	INTEGER,
	"from_addr"	TEXT,
	"to_addr"	TEXT,
	"value"	NUMERIC,
	"gas"	NUMERIC,
	"args"	TEXT,
	"timestamps"	TEXT,
	"tx_hash"	TEXT
);
CREATE TABLE IF NOT EXISTS "non_mined_transactions" (
	"from_addr"	TEXT,
	"to_addr"	TEXT,
	"value"	NUMERIC,
	"gas"	NUMERIC,
	"args"	TEXT,
	"timestamp"	TEXT,
	"tx_hash"	TEXT
);
CREATE TABLE IF NOT EXISTS "Profile" (
	"name"	TEXT,
	"email"	TEXT,
	"u_name"	TEXT,
	"password"	TEXT,
	"private_key"	TEXT,
	"public_key"	TEXT
);
CREATE TABLE IF NOT EXISTS "connected_nodes" (
	"address"	TEXT,
	"port"	TEXT,
	"public_key"	TEXT
);
CREATE TABLE IF NOT EXISTS "Chain" (
	"ind"	INTEGER,
	"timestamp"	TEXT,
	"data"	TEXT,
	"difficulty"	INTEGER,
	"merkle_root"	TEXT,
	"prev_hash"	TEXT,
	"nonce"	INTEGER,
	"hash"	INTEGER,
	PRIMARY KEY("hash","ind")
);
CREATE TABLE IF NOT EXISTS "Contracts" (
	"c_address"	TEXT,
	"start_time"	REAL,
	"end_time"	REAL
);
CREATE TABLE IF NOT EXISTS "State" (
	"public_key"	TEXT,
	"balance"	NUMERIC,
	"body"	TEXT,
	"used_timestamps"	TEXT,
	"storage"	TEXT,
	PRIMARY KEY("public_key")
);
INSERT INTO "mined_transactions" ("block_index","from_addr","to_addr","value","gas","args","timestamps","tx_hash") VALUES (0,NULL,'-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC9NGmSYdh1s0OpYgiVWQ+YEdx6
lSXm4b78fJrlBxbx7DoNXjuluX+KdIm6zzsb40HbTwBJT3n53BSC981Cx28z7tUp
ujO3dSGt8rIQsitb5pl5yTgcaggyD/xYriNDZsU8sP2AdEUlLs2Xg/ap5OHII0dh
hSQXq0JuWAJUFG0gqQIDAQAB
-----END PUBLIC KEY-----',0,0,'["Initial Blockchain Transaction"]','1640995200.0','3c3145cc66f5e9dcb469ad7ca232ec4ac56ad489a5c8ecbc68ad34f7d5b1b6eb');
INSERT INTO "Profile" ("name","email","u_name","password","private_key","public_key") VALUES ('John Smith','smith@gmail.com','John','1234','-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQCrtZvN0y9WOQaEtxlcjMg+uA+Edc3JVBAVQkkC4LDSBmjw73l6
ircSRFG+gRlleyY5iRt3ug7mkQddw1YB5rctdwnxQRJezdSrKcluraWqfn/+MghB
3BXb9qstENn5HE4o8AARXaRVvDhuG8i3fC/TcPG/Wn8eJ4tz/S4TxgBx5QIDAQAB
AoGAKVbFtd3cDaQY/6adQnzaUM87XSaHbqsAXD3jGgBCUa4dYbQlyOzQemNcUsL9
/EKTx1JM/JwcrkHIRjia4kZLXw+XHr4LWFxe6LYdN+zlDCQMyVv73w53VsP5sMN+
VA5cUZhfM+ZEfyTEhNVxLcFH9IiGK3oRzfMiLYrg2acgXVkCQQDEPa5h5u5miP6M
eDJbv4RecrrgnDmI1EGe/Sa/T+zcadL4gmEvfkutgid8Rrd3ltgz6G6qMEyHS1OO
udKXqc23AkEA3/+G90dfRj2bEyUzMxaD9BlgYYehfCMctM355z85kkbrnbh70G0E
fOskz4Bj/V2qVQnE/IuQviKWA5bONc09QwJAcSgYC7/7rAhGr30HnLv8efGyLJ4o
1ut9w026MArIS/iBfGbB33716GDqn9CvLjg/Bv96AIzFNCaNUfl4o5d4VQJBAM1o
g5nLB2FgKQ7bdCILKaH0i1+kgr9Va4OZxur6HY84HeSaQmAVOKJc93qZIBg9hm9I
8C0uxuK00KAl8J+BwAUCQQCqW/hjM1P7wiAckHzVdjcYmPG2R/yXBfaoSRt4FUd6
2erTVr6M70fQYAIqTM4de6oSAje5yTJzNWCFKCR24jLs
-----END RSA PRIVATE KEY-----','-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCrtZvN0y9WOQaEtxlcjMg+uA+E
dc3JVBAVQkkC4LDSBmjw73l6ircSRFG+gRlleyY5iRt3ug7mkQddw1YB5rctdwnx
QRJezdSrKcluraWqfn/+MghB3BXb9qstENn5HE4o8AARXaRVvDhuG8i3fC/TcPG/
Wn8eJ4tz/S4TxgBx5QIDAQAB
-----END PUBLIC KEY-----');
INSERT INTO "Chain" ("ind","timestamp","data","difficulty","merkle_root","prev_hash","nonce","hash") VALUES (0,'1640995200.0','[{"from_addr": null, "to_addr": "-----BEGIN PUBLIC KEY-----\nMIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC9NGmSYdh1s0OpYgiVWQ+YEdx6\nlSXm4b78fJrlBxbx7DoNXjuluX+KdIm6zzsb40HbTwBJT3n53BSC981Cx28z7tUp\nujO3dSGt8rIQsitb5pl5yTgcaggyD/xYriNDZsU8sP2AdEUlLs2Xg/ap5OHII0dh\nhSQXq0JuWAJUFG0gqQIDAQAB\n-----END PUBLIC KEY-----", "value": 0, "gas": 0, "args": "[\"Initial Blockchain Transaction\"]", "timestamp": 1640995200.0, "tx_hash": "3c3145cc66f5e9dcb469ad7ca232ec4ac56ad489a5c8ecbc68ad34f7d5b1b6eb"}]',4,'ec9af1b70eec9eebfb5a31876becb83c93461d3e34d31792cd54a4854e7c682f','0000000000000000000000000000000000000000000000000000000000000000',30089,'0000ba46b5ba0a16f78724142118dcf1795a1c09edcd084adf1a2198cbfaf1b9');
INSERT INTO "State" ("public_key","balance","body","used_timestamps","storage") VALUES ('-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC9NGmSYdh1s0OpYgiVWQ+YEdx6
lSXm4b78fJrlBxbx7DoNXjuluX+KdIm6zzsb40HbTwBJT3n53BSC981Cx28z7tUp
ujO3dSGt8rIQsitb5pl5yTgcaggyD/xYriNDZsU8sP2AdEUlLs2Xg/ap5OHII0dh
hSQXq0JuWAJUFG0gqQIDAQAB
-----END PUBLIC KEY-----',0,'','[]','{}');
COMMIT;
