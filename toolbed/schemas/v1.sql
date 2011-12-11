CREATE TABLE `version`
(
 `version` INTEGER -- contains one row, set to 1
);

CREATE TABLE `node` -- contains one row
(
 `webport` STRING,
 `relay_location` STRING
);

CREATE TABLE `services`
(
 `name` STRING
);

CREATE TABLE `webui_initial_nonces`
(
 `nonce` STRING
);

CREATE TABLE `relay_config` -- contains one row
(
 `relayport` STRING
);
