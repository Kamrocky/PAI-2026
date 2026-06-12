
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE accounts (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    balance DECIMAL(12, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'PLN',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(50) NOT NULL,
    icon VARCHAR(30), -- np. nazwa ikonki z FontAwesome lub Lucide
    color VARCHAR(7), -- kod HEX dla wykresów na dashboardzie
    is_income BOOLEAN DEFAULT FALSE -- rozróżnienie czy to kategoria przychodowa czy kosztowa
);

CREATE TABLE transactions (
    id SERIAL PRIMARY KEY,
    account_id INTEGER REFERENCES accounts(id) ON DELETE CASCADE,
    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
    amount DECIMAL(12, 2) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT,
    transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO users (username, email, password_hash) VALUES 
('testuser', 'test@example.com', 'scrypt_hash_here');

INSERT INTO accounts (user_id, name, balance) VALUES 
(1, 'Główne konto bankowe', 5000.00),
(1, 'Gotówka w portfelu', 250.00);

INSERT INTO categories (user_id, name, color, is_income) VALUES 
(1, 'Jedzenie', '#FF5733', FALSE),
(1, 'Mieszkanie', '#3357FF', FALSE),
(1, 'Wynagrodzenie', '#2ECC71', TRUE),
(1, 'Transport', '#F1C40F', FALSE);

INSERT INTO transactions (account_id, category_id, amount, title) VALUES 
(1, 3, 4500.00, 'Wypłata luty'),
(1, 1, -150.50, 'Zakupy w Biedronce'),
(2, 4, -45.00, 'Bilet miesięczny');