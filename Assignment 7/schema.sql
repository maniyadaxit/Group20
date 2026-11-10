-- CampusEats / CampusEats Catalogue GraphQL service
-- Standalone schema for the Assignment 7 demo.
CREATE DATABASE IF NOT EXISTS campuseats_catalogue
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE campuseats_catalogue;

CREATE TABLE IF NOT EXISTS menu_items (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  price DECIMAL(10,2) NOT NULL,
  is_available BOOLEAN NOT NULL DEFAULT TRUE,
  category VARCHAR(60) NULL,
  description VARCHAR(500) NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT chk_menu_item_price CHECK (price >= 0),
  INDEX idx_menu_items_available (is_available),
  INDEX idx_menu_items_category (category)
);

INSERT INTO menu_items (name, price, is_available, category, description)
SELECT 'Paneer Wrap', 110.00, TRUE, 'Wraps', 'Paneer, fresh vegetables and house sauce'
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = 'Paneer Wrap');
INSERT INTO menu_items (name, price, is_available, category, description)
SELECT 'Masala Fries', 75.00, TRUE, 'Sides', 'Crispy fries with masala seasoning'
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = 'Masala Fries');
INSERT INTO menu_items (name, price, is_available, category, description)
SELECT 'Cold Coffee', 90.00, TRUE, 'Drinks', 'Chilled coffee'
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = 'Cold Coffee');
INSERT INTO menu_items (name, price, is_available, category, description)
SELECT 'Veg Sandwich', 85.00, FALSE, 'Snacks', 'Grilled vegetable sandwich'
WHERE NOT EXISTS (SELECT 1 FROM menu_items WHERE name = 'Veg Sandwich');
