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

CREATE TABLE `client_profile` -- contains one row
(
 `name` STRING,
 `icon_data` STRING
);

-- outbound_invitations are created as soon as the user starts the invitation
-- process. stage=0 means the user has been told the invitation code (with
-- instructions to send "M0" to the recipient), but our node is still waiting
-- for the recipient's first message (M1). stage=2 means M1 has been received
-- and M2 was sent, still waiting for M3 (the ACK) to arrive. When M3
-- arrives, the invitation is complete and the whole row is removed.

CREATE TABLE `outbound_invitations`
(
 `sent` INTEGER, -- seconds-since-epoch from the "send" button being pressed
 `expires` INTEGER, -- when the invitation expires
 `petname` STRING,
 `code` STRING, -- invitation code (sent to recipient)
 `stage` INTEGER,
 `abob` STRING, -- addressbook entry for us
 `balice` STRING -- our addressbook entry for them
);

-- inbound invitations are created when M0 is pasted in by the user and M1 is
-- sent, so we're waiting for M2 to arrive. After M2 arrives, we complete the
-- invitation, send M3, and delete the row. We don't need to store Balice in
-- the DB because we add the addressbook entry as soon as we learn it (the
-- sender waits for an ACK, not us)
CREATE TABLE `inbound_invitations`
(
 `petname` STRING,
 `code` STRING,
 `address` STRING -- our address
);

CREATE TABLE `addressbook`
(
 `petname` STRING,
 `key` STRING
);
