CREATE DATABASE IF NOT EXISTS carrent;
USE carrent;

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

CREATE TABLE if not exists cars (
  id int NOT NULL,
  brand varchar(100) NOT NULL,
  model varchar(100) NOT NULL,
  year int NOT NULL,
  category varchar(50) NOT NULL,
  image_url varchar(255) DEFAULT NULL,
  price decimal(10,2) NOT NULL DEFAULT 0.00,
  location varchar(100) DEFAULT NULL,
  availability_status varchar(20) DEFAULT 'Available',
  transmission varchar(20) DEFAULT NULL,
  seats int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO cars (id, brand, model, year, category, image_url, price, location, availability_status, transmission, seats) VALUES
(22, 'Toyota ', 'Raize ', 2022, 'LSUV', 'uploads/raize.jpg', 350000.00, 'Jakarta', 'Unavailable', 'Automatic', 5),
(23, 'Toyota ', 'Avanza', 2022, 'LMPV', 'uploads/avanza.jpg', 350000.00, 'Bogor', 'Available', 'Automatic', 8),
(24, 'Honda', 'Jazz ', 2012, 'Hatchback', 'uploads/jazz.jpg', 300000.00, 'Jakarta', 'Available', 'Manual', 5),
(27, 'Suzuki', 'Ertiga', 2019, 'LMPV', 'uploads/ertiga.jpeg', 300000.00, 'Bogor', 'Unavailable', 'Automatic', 7),
(29, 'Hyundai', 'Creta', 2023, 'LSUV', 'uploads/creta.jpeg', 400000.00, 'Bogor', 'Available', 'Automatic', 5),
(30, 'Wuling', 'Confero', 2021, 'LMPV', 'uploads/confero.jpeg', 280000.00, 'Jakarta', 'Available', 'Manual', 7),
(31, 'Toyota', 'Fortuner', 2022, 'LSUV', 'uploads/fortuner.jpeg', 600000.00, 'Jakarta', 'Unavailable', 'Automatic', 7),
(32, 'Honda', 'Brio', 2022, 'Hatchback', 'uploads/brio.jpeg', 275000.00, 'Jakarta', 'Available', 'CVT', 5),
(33, 'Mazda', 'CX-5', 2021, 'LSUV', 'uploads/cx5.jpeg', 500000.00, 'Jakarta', 'Available', 'Automatic', 5),
(34, 'Wuling', 'Almaz', 2023, 'LSUV', 'uploads/almaz.jpeg', 350000.00, 'Jakarta', 'Available', 'Manual', 7);

CREATE TABLE if not exists rentals (
  id int NOT NULL,
  user_id int NOT NULL,
  car_id int NOT NULL,
  status enum('pending','approved','rejected','canceled','ongoing','completed') DEFAULT NULL,
  request_date timestamp NOT NULL DEFAULT current_timestamp(),
  start_date date DEFAULT NULL,
  end_date date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO rentals (id, user_id, car_id, status, request_date, start_date, end_date) VALUES
(42, 10, 23, 'completed', '2025-03-19 19:17:55', '2025-03-22', '2025-03-24'),
(43, 1, 22, 'approved', '2025-03-20 21:29:14', '2025-03-23', '2025-03-28');

CREATE TABLE if not exists transaction_history (
  id int NOT NULL,
  user_id int DEFAULT NULL,
  rental_id int DEFAULT NULL,
  email varchar(255) DEFAULT NULL,
  status enum('pending','approved','rejected') DEFAULT NULL,
  created_at timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE if not exists users (
  id int NOT NULL,
  username varchar(100) NOT NULL,
  password varchar(255) NOT NULL,
  role enum('admin','member') NOT NULL,
  gender varchar(20) DEFAULT NULL,
  first_name varchar(100) DEFAULT NULL,
  last_name varchar(100) DEFAULT NULL,
  birth_date date DEFAULT NULL,
  email varchar(100) DEFAULT NULL,
  country_code varchar(10) DEFAULT NULL,
  phone_number varchar(20) DEFAULT NULL,
  country varchar(100) DEFAULT NULL,
  address text DEFAULT NULL,
  postal_code varchar(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

INSERT INTO users (id, username, password, role, gender, first_name, last_name, birth_date, email, country_code, phone_number, country, address, postal_code) VALUES
(1, '1', 'scrypt:32768:8:1$06AbfUjHtWHPJcju$e2e0bfdc80dcabe32a863ec70856f9c28bebdac1556adad8fb6a4171f850ce0d84d3f1a61adf09e6624d2dd5647889a42512484e34a3eacaaefbd336649710fd', 'member', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(6, 'admin', 'pbkdf2:sha256:1000000$XfsR5QkaUHb0KTYt$e8702d01d7f59eaa6a7f26dcd4e760786ce200b2426169222573ad22341def19', 'admin', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(7, '2', 'scrypt:32768:8:1$Ol05Lpzh9hbg3A2A$d54ef222b088687011fd907d18934a86bbb4bce185add40f90c0e21d6c68b47032598d95f75794089053d11d6d2c646f3b848234386328d065d337e50026e60c', 'member', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL),
(10, 'kenahnaf', 'scrypt:32768:8:1$eXxgIpMc4LlvTaRX$680853eeeebbe0e8eed09c098d5553b8f3a20f33d1bff6c16993d0fcba06206ad8f795c5f0940abc37dc1cf3d5d497427d44c085c1f57a26374165913be17256', 'member', 'Laki-laki', 'ken', 'ahnaf', '2004-11-18', 'kenanargya5@gmail.com', '+62', '82226976976', 'Indonesia', 'Jl. raya', '55584');

ALTER TABLE cars
  ADD PRIMARY KEY (id);

ALTER TABLE rentals
  ADD PRIMARY KEY (id),
  ADD KEY user_id (user_id),
  ADD KEY car_id (car_id);

ALTER TABLE transaction_history
  ADD PRIMARY KEY (id),
  ADD KEY user_id (user_id),
  ADD KEY rental_id (rental_id);

ALTER TABLE users
  ADD PRIMARY KEY (id);

ALTER TABLE cars
  MODIFY id int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=25;

ALTER TABLE rentals
  MODIFY id int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=44;

ALTER TABLE transaction_history
  MODIFY id int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

ALTER TABLE users
  MODIFY id int NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

ALTER TABLE rentals
  ADD CONSTRAINT rentals_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE,
  ADD CONSTRAINT rentals_ibfk_2 FOREIGN KEY (car_id) REFERENCES cars (id) ON DELETE CASCADE;

ALTER TABLE transaction_history
  ADD CONSTRAINT transaction_history_ibfk_1 FOREIGN KEY (user_id) REFERENCES users (id),
  ADD CONSTRAINT transaction_history_ibfk_2 FOREIGN KEY (rental_id) REFERENCES rentals (id);
  
select * from users;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
