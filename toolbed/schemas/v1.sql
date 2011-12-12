CREATE TABLE `version`
(
 `version` INTEGER -- contains one row, set to 1
);

CREATE TABLE `node` -- contains one row
(
 `webport` STRING
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

CREATE TABLE `client_config` -- contains one row
(
 `privkey` STRING,
 `pubkey` STRING,
 `relay_location` STRING
);

CREATE TABLE `pending_invitations`
(
 `sent` INTEGER, -- seconds-since-epoch from the "send" button being pressed
 `expires` INTEGER, -- when the invitation expires
 `petname` STRING,
 `private_code` STRING,
 `code` STRING -- invitation code (sent to recipient)
);
