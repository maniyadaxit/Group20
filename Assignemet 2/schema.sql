-- =====================================================================
-- CampusEats — Database Schema (schema.sql)
-- CS 543 Web Services — Assignment 2, Task 5
--
-- Grouped strictly by the 5 service boundaries. No table belongs to two
-- services. Cross-service references are LOGICAL ONLY: the column stores
-- the foreign ID as plain data, with no DB-level FOREIGN KEY constraint
-- across a service boundary. Only within-service references use real
-- SQL FOREIGN KEY constraints.
-- =====================================================================


-- =====================================================================
-- IDENTITY SERVICE
-- =====================================================================

CREATE TABLE users (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(120)    NOT NULL,
    email           VARCHAR(160)    NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    role            ENUM('STUDENT','VENDOR','DELIVERY_PARTNER','ADMIN') NOT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- =====================================================================
-- CATALOGUE SERVICE
-- =====================================================================

CREATE TABLE vendors (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    owner_user_id   INTEGER         NOT NULL, -- logical ref -> Identity.users.id (no cross-service FK)
    name            VARCHAR(120)    NOT NULL,
    type            ENUM('CANTEEN','MESS','CAFE','EXTERNAL') NOT NULL,
    location        VARCHAR(200),
    opening_hours   VARCHAR(100),
    is_active       BOOLEAN         NOT NULL DEFAULT TRUE
);

CREATE TABLE menu_items (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    vendor_id       INTEGER         NOT NULL,
    name            VARCHAR(120)    NOT NULL,
    description     VARCHAR(500),
    price           DECIMAL(10,2)   NOT NULL,
    category        VARCHAR(60),
    is_available    BOOLEAN         NOT NULL DEFAULT TRUE,
    image_url       VARCHAR(300),
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);

CREATE TABLE reviews (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_id        INTEGER         NOT NULL, -- logical ref -> Orders.orders.id (no cross-service FK)
    vendor_id       INTEGER         NOT NULL,
    vendor_rating   TINYINT         NOT NULL,
    comment         VARCHAR(1000),
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vendor_id) REFERENCES vendors(id)
);


-- =====================================================================
-- ORDERS SERVICE
-- =====================================================================

CREATE TABLE carts (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    student_id      INTEGER         NOT NULL, -- logical ref -> Identity.users.id
    vendor_id       INTEGER         NOT NULL, -- logical ref -> Catalogue.vendors.id
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE cart_items (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    cart_id         INTEGER         NOT NULL,
    menu_item_id    INTEGER         NOT NULL, -- logical ref -> Catalogue.menu_items.id
    quantity        INTEGER         NOT NULL DEFAULT 1,
    price_snapshot  DECIMAL(10,2)   NOT NULL,
    FOREIGN KEY (cart_id) REFERENCES carts(id)
);

CREATE TABLE orders (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    student_id      INTEGER         NOT NULL, -- logical ref -> Identity.users.id
    vendor_id       INTEGER         NOT NULL, -- logical ref -> Catalogue.vendors.id
    status          ENUM('PLACED','CONFIRMED','PREPARING','READY','COMPLETED','CANCELLED') NOT NULL DEFAULT 'PLACED',
    delivery_type   ENUM('PICKUP','DELIVERY') NOT NULL,
    time_slot       VARCHAR(40),
    total_amount    DECIMAL(10,2)   NOT NULL,
    coupon_code     VARCHAR(40),
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_items (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_id        INTEGER         NOT NULL,
    menu_item_id    INTEGER         NOT NULL, -- logical ref -> Catalogue.menu_items.id
    quantity        INTEGER         NOT NULL DEFAULT 1,
    price_at_order  DECIMAL(10,2)   NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(id)
);


-- =====================================================================
-- PAYMENTS SERVICE
-- =====================================================================

CREATE TABLE payments (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_id        INTEGER         NOT NULL, -- logical ref -> Orders.orders.id
    amount          DECIMAL(10,2)   NOT NULL,
    method          ENUM('WALLET','CARD','UPI') NOT NULL,
    status          ENUM('PENDING','SUCCESS','FAILED','REFUNDED') NOT NULL DEFAULT 'PENDING',
    transaction_ref VARCHAR(100),
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE wallets (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    user_id         INTEGER         NOT NULL UNIQUE, -- logical ref -> Identity.users.id
    balance         DECIMAL(10,2)   NOT NULL DEFAULT 0
);

CREATE TABLE wallet_transactions (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    wallet_id       INTEGER         NOT NULL,
    amount          DECIMAL(10,2)   NOT NULL,
    type            ENUM('CREDIT','DEBIT') NOT NULL,
    reference       VARCHAR(100),
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (wallet_id) REFERENCES wallets(id)
);

CREATE TABLE coupons (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    code            VARCHAR(40)     NOT NULL UNIQUE,
    discount_type   ENUM('PERCENT','FLAT') NOT NULL,
    value           DECIMAL(10,2)   NOT NULL,
    valid_from      DATE            NOT NULL,
    valid_to        DATE            NOT NULL,
    usage_limit     INTEGER
);

CREATE TABLE subscriptions (
    id                  INTEGER PRIMARY KEY AUTO_INCREMENT,
    student_id          INTEGER     NOT NULL, -- logical ref -> Identity.users.id
    vendor_id           INTEGER     NOT NULL, -- logical ref -> Catalogue.vendors.id
    plan_type           VARCHAR(60) NOT NULL,
    start_date          DATE        NOT NULL,
    end_date            DATE        NOT NULL,
    remaining_credits   INTEGER     NOT NULL DEFAULT 0
);


-- =====================================================================
-- DELIVERY SERVICE
-- =====================================================================

CREATE TABLE deliveries (
    id                      INTEGER PRIMARY KEY AUTO_INCREMENT,
    order_id                INTEGER     NOT NULL, -- logical ref -> Orders.orders.id
    delivery_partner_id     INTEGER     NOT NULL, -- logical ref -> Identity.users.id
    status                  ENUM('ASSIGNED','PICKED_UP','ON_THE_WAY','DELIVERED') NOT NULL DEFAULT 'ASSIGNED',
    drop_zone               VARCHAR(100),
    created_at              TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE delivery_zones (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    name            VARCHAR(100)    NOT NULL,
    building_type   ENUM('HOSTEL','ACADEMIC','OTHER') NOT NULL
);

CREATE TABLE tracking_updates (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    delivery_id     INTEGER         NOT NULL,
    status          VARCHAR(60)     NOT NULL,
    timestamp       TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (delivery_id) REFERENCES deliveries(id)
);
