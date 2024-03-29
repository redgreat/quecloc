CREATE DATABASE IF NOT EXISTS `dailywong` CACHEMODEL 'both' CACHESIZE 32 COMP 2 KEEP 365000;

SHOW CREATE DATABASE `dailywong` \G;

SELECT * FROM INFORMATION_SCHEMA.INS_DATABASES WHERE NAME='dailywong' \G;

CREATE STABLE `locdaily` (`LocTime` TIMESTAMP, `Lat` FLOAT, `Lng` FLOAT) TAGS (`DeviceIMEI` VARCHAR(50));

INSERT INTO `dailywong`.`123` USING `dailywong`.`locdaily`(`DeviceIMEI`) TAGS('123')(`LocTime`, `Lat`, `Lng`)
VALUES ('')