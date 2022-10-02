BEGIN TRANSACTION;
CREATE TABLE IF NOT EXISTS "board" (
	"name"	TEXT,
	"email"	TEXT,
	"uname"	TEXT,
	"pword"	TEXT,
	"private_key"	TEXT,
	"public_key"	TEXT
);
CREATE TABLE IF NOT EXISTS "Parliament" (
	"party_id"	TEXT,
	"name"	TEXT,
	"age"	TEXT,
	"constituency"	TEXT,
	"description"	TEXT
);
CREATE TABLE IF NOT EXISTS "President" (
	"party_id"	TEXT,
	"name"	TEXT,
	"portfolio"	TEXT,
	"age"	TEXT,
	"desc"	TEXT
);
INSERT INTO "board" ("name","email","uname","pword","private_key","public_key") VALUES ('User One','one@gmail.com','userone','userone','-----BEGIN RSA PRIVATE KEY-----
MIICWwIBAAKBgQCofnA63FjJ2bOznmRAyRYFPjzZgaoJ9Gx8Jg4jBScucEMO+Lvs
ckrDsvwpgKMnmuxhIyIwfmgX4y4Tnc+Py+TkgkpZ0qMXdzhnqTttB44Ku+pxNll0
/fZrR/DVJtZwuc9jrPQyzGdRE59x24Ux8EhNFMNBaeO8p+qhe1sp4IU9dwIDAQAB
AoGAOkkGrK3VfvmyepNzjZ+h4O1vIjSC7A+jyWxmnoGlVKCb6d1sMHY226yaIwcv
KT+jvlRnesv3WTAKm9mO1+jJxBwYDoOrWE20zOzp99O51QyuAAAKEm6+9NdqRfl7
kYkTPzsVxMTuAZXSJ3yCfbCO0fwYhx8YsBjg/eO7CH6HpdUCQQDAIYZkLYGMxu0L
g62ozGFzRDeupH0nqnV/70lxVKNSQQ2xPDxtzjcWymTi2kIRzHmWkjXI+kOvla2z
Y2gIDC+1AkEA4IFiQifrCS9lPj++FhbegPrdCnPyqWOMa7gbrRaVKAovc1TRhVPE
ZnlJZlaAve2bH4jVkNKgT7RM9uecyhz7+wJABt/sOB9suEXR64yNpTGS9xXkzCn0
lHvD8oz0WsrFgUb0n3fhTaiIThd13qwimxJu81VN+WADFgBME9Qlv8v31QJAdWOx
2R2+TAM4USBLaIl0tsR1p+2QyPmAhyKxdgQE4fbRcOC83ZY7b8mjk5tPngALyKVn
5l377TE9vSzGUvhs2QJAIq++pKz66a69RLTuCqLbuiy5Z/boGOYxde75QMRfAWQt
KOCvG6niqXeGiCbaapiLpiypc9uCW2Xbw3WpeD3oLw==
-----END RSA PRIVATE KEY-----','-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCofnA63FjJ2bOznmRAyRYFPjzZ
gaoJ9Gx8Jg4jBScucEMO+LvsckrDsvwpgKMnmuxhIyIwfmgX4y4Tnc+Py+TkgkpZ
0qMXdzhnqTttB44Ku+pxNll0/fZrR/DVJtZwuc9jrPQyzGdRE59x24Ux8EhNFMNB
aeO8p+qhe1sp4IU9dwIDAQAB
-----END PUBLIC KEY-----');
COMMIT;
