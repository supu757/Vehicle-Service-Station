-- phpMyAdmin SQL Dump
-- version 5.2.3
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 26, 2026 at 03:24 AM
-- Server version: 10.11.19-MariaDB
-- PHP Version: 8.5.13

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `vehicle_service_db`
--

-- --------------------------------------------------------

--
-- Table structure for table `appointments`
--

CREATE TABLE `appointments` (
  `appointment_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `vehicle_id` int(11) NOT NULL,
  `booking_date` date NOT NULL,
  `time_slot` varchar(20) NOT NULL,
  `service_type` varchar(100) NOT NULL,
  `status` enum('Pending','Confirmed','Cancelled','Completed') DEFAULT 'Pending',
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `appointments`
--

INSERT INTO `appointments` (`appointment_id`, `customer_id`, `vehicle_id`, `booking_date`, `time_slot`, `service_type`, `status`, `created_at`) VALUES
(1, 1, 1, '2026-11-28', '08:30 AM - 10:30 AM', 'Full Service', 'Completed', '2026-11-26 02:00:04');

-- --------------------------------------------------------

--
-- Table structure for table `feedback`
--

CREATE TABLE `feedback` (
  `feedback_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `rating` int(11) NOT NULL,
  `comments` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `invoices`
--

CREATE TABLE `invoices` (
  `invoice_id` int(11) NOT NULL,
  `appointment_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `labor_charge` decimal(10,2) DEFAULT 0.00,
  `parts_charge` decimal(10,2) DEFAULT 0.00,
  `total_amount` decimal(10,2) NOT NULL,
  `payment_status` enum('Unpaid','Paid') DEFAULT 'Unpaid',
  `payment_date` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `invoices`
--

INSERT INTO `invoices` (`invoice_id`, `appointment_id`, `customer_id`, `labor_charge`, `parts_charge`, `total_amount`, `payment_status`, `payment_date`, `created_at`) VALUES
(1, 1, 1, 6500.00, 0.00, 6500.00, 'Paid', '2026-11-26 07:45:28', '2026-11-26 02:15:28');

-- --------------------------------------------------------

--
-- Table structure for table `job_cards`
--

CREATE TABLE `job_cards` (
  `job_card_id` int(11) NOT NULL,
  `appointment_id` int(11) NOT NULL,
  `technician_id` int(11) DEFAULT NULL,
  `inspection_notes` text DEFAULT NULL,
  `job_status` enum('Pending','Inspection','In Progress','Completed') DEFAULT 'Pending',
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `job_cards`
--

INSERT INTO `job_cards` (`job_card_id`, `appointment_id`, `technician_id`, `inspection_notes`, `job_status`, `created_at`) VALUES
(1, 1, 6, 'Technician assigned by Service Officer', 'Completed', '2026-11-26 02:04:47');

-- --------------------------------------------------------

--
-- Table structure for table `job_parts`
--

CREATE TABLE `job_parts` (
  `part_id` int(11) NOT NULL,
  `job_card_id` int(11) NOT NULL,
  `part_name` varchar(150) NOT NULL,
  `quantity` int(11) NOT NULL DEFAULT 1,
  `unit_price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `total_price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `added_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Table structure for table `services`
--

CREATE TABLE `services` (
  `service_id` int(11) NOT NULL,
  `service_name` varchar(150) NOT NULL,
  `base_price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `description` varchar(255) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `services`
--

INSERT INTO `services` (`service_id`, `service_name`, `base_price`, `description`, `created_at`) VALUES
(1, 'Full Service', 6500.00, 'Complete vehicle lubrication, filter check & undercarriage inspection', '2026-11-25 11:27:39'),
(2, 'Oil & Filter Change', 2500.00, 'Engine oil draining, refill & oil filter replacement', '2026-11-25 11:27:39'),
(3, 'Body Wash & Interior Vacuum', 1800.00, 'Exterior foam wash, waxing & interior vacuum cleaning', '2026-11-25 11:27:39'),
(4, 'Brake Service & Inspection', 3500.00, 'Brake pad/shoe cleaning, adjustment & fluid check', '2026-11-25 11:27:39'),
(5, 'Wheel Alignment & Balancing', 3000.00, '4-wheel computerized alignment and wheel balancing', '2026-11-25 11:27:39'),
(6, 'Engine Tune-Up & Diagnostics', 5500.00, 'OBD scanning, spark plug & injector inspection', '2026-11-25 11:27:39'),
(7, 'AC Service & Gas Refill', 4800.00, 'AC system pressure check, filter cleaning & refrigerant top-up', '2026-11-25 11:27:39'),
(8, 'Battery & Electrical Check', 1500.00, 'Alternator, starter motor & battery health diagnostics', '2026-11-25 11:27:39');

-- --------------------------------------------------------

--
-- Table structure for table `spare_parts`
--

CREATE TABLE `spare_parts` (
  `part_id` int(11) NOT NULL,
  `part_name` varchar(150) NOT NULL,
  `stock_qty` int(11) NOT NULL DEFAULT 0,
  `unit_price` decimal(10,2) NOT NULL DEFAULT 0.00,
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `spare_parts`
--

INSERT INTO `spare_parts` (`part_id`, `part_name`, `stock_qty`, `unit_price`, `created_at`) VALUES
(1, 'Oil Filter', 25, 2200.00, '2026-11-25 11:34:29'),
(2, 'Air Filter', 20, 3500.00, '2026-11-25 11:34:29'),
(3, 'Fuel Filter', 15, 4500.00, '2026-11-25 11:34:29'),
(4, 'Cabin AC Filter', 18, 4000.00, '2026-11-25 11:34:29'),
(5, 'Spark Plugs (Set of 4)', 30, 6000.00, '2026-11-25 11:34:29'),
(6, 'Brake Pads (Front)', 12, 12500.00, '2026-11-25 11:34:29'),
(7, 'Brake Pads (Rear)', 10, 11000.00, '2026-11-25 11:34:29'),
(8, 'Engine Oil 4L', 40, 14500.00, '2026-11-25 11:34:29'),
(9, 'Coolant 1L', 25, 2800.00, '2026-11-25 11:34:29'),
(10, 'Gear Oil 1L', 15, 3200.00, '2026-11-25 11:34:29');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `role` varchar(50) DEFAULT 'Customer',
  `created_at` timestamp NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `full_name`, `email`, `password_hash`, `phone`, `role`, `created_at`) VALUES
(1, 'S.K.S.Udeshika', 'supuniudeshika297@gmail.com', 'scrypt:32768:8:1$ne7WRWkjdcX3uadU$531a12eb11b9932ca5700c15ca47dd5e9a6536f96200b45d88419b7ca9586e5d1f17e2e2a61a779d82c33ebdf650f39cef11a78bdf5a79c5f89adc84f9f13bb7', '0740517117', 'Customer', '2026-11-25 10:34:49'),
(2, 'G.I.S.Senarathna', 'shanmaxishan2004@gmail.com', 'scrypt:32768:8:1$JRuGnE7AYjkiiJKN$1117145fcae8844b6b035e2a633625671b265563fbc15e57d8cc3412bd04febea840eb964c8589db0813668ba0984b97e251c4909ab1395bdceefd1858696cf7', '0775196078', 'Service Officer', '2026-11-25 11:56:43'),
(3, 'S.K.Chamara', 'chamarapushpa456@gmail.com', 'scrypt:32768:8:1$4LvnmRDvxmYS5s4N$01c8e6732c068203dd115af0b30601177a34ae24188b57978216da4f217bcec03128efbae168c6b12671d3d024348240c60df3e20a4e33ff5bae6dc9e91b6edb', '0703828010', 'Admin', '2026-11-25 12:10:20'),
(4, 'Nimal Perara', 'nimal123@gmail.com', 'scrypt:32768:8:1$lOFhJYACXP6r08C4$be07fa09e10d909ac90c62948cd917bf92236f5da2e9746691ea9d77aea71cef5f1fb45fd66c1e5b8be20c814ab4acc7dff960b6d832fc7f7006c55bbba529a1', '0748956231', 'Technician', '2026-11-25 12:14:40'),
(5, 'Tharusha Devinda', 'tharushadevinda89@gmail.com', 'scrypt:32768:8:1$a2NcuIwoH65g7aKZ$fbfabfea1ff410e6862607d31a58976aad719f744a6196624f6213fc2fde524d7de80a8e60ba2e66a8a7a2b87152905b1ebedc8497a5620d50a4973686351fba', '0717582506', 'Technician', '2026-11-25 12:20:40'),
(6, 'Kavindu Methsara', 'kavindumethsara63@gmail.com', 'scrypt:32768:8:1$JSriIQbdWLngkhAQ$9e15f2727c9f1cfb0430a8026bcd5e71a5763b5207cbf32c467945d408817e56ef583b47222359c2e54ecd738cc955a931bae3e714bcbde80de32c74e45a185a', '0763857584', 'Technician', '2026-11-25 12:33:16'),
(7, 'Udeshi', 'udeshi789@gmail.com', 'scrypt:32768:8:1$wpuEvMp0J6bkpv3D$7ebc5e9e9518c67dec1b30ab23be81f471be783a2e185838087f15a0d25412c9b5a03894769c4344fe3588b71eea4dc44019eeb015b67584da23a7ecfddf2b31', '0772536456', 'Owner', '2026-11-25 12:41:23');

-- --------------------------------------------------------

--
-- Table structure for table `vehicles`
--

CREATE TABLE `vehicles` (
  `vehicle_id` int(11) NOT NULL,
  `customer_id` int(11) NOT NULL,
  `license_plate` varchar(20) NOT NULL,
  `make_model` varchar(100) NOT NULL,
  `year` int(11) DEFAULT NULL,
  `chassis_number` varchar(100) DEFAULT NULL,
  `colour` varchar(50) DEFAULT NULL,
  `mileage` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `vehicles`
--

INSERT INTO `vehicles` (`vehicle_id`, `customer_id`, `license_plate`, `make_model`, `year`, `chassis_number`, `colour`, `mileage`) VALUES
(1, 1, 'CAG 0002', 'TATA Indica', 2018, 'Ab457PTHLM789', 'Silver', 28500);

--
-- Indexes for dumped tables
--

--
-- Indexes for table `appointments`
--
ALTER TABLE `appointments`
  ADD PRIMARY KEY (`appointment_id`),
  ADD KEY `customer_id` (`customer_id`),
  ADD KEY `vehicle_id` (`vehicle_id`);

--
-- Indexes for table `feedback`
--
ALTER TABLE `feedback`
  ADD PRIMARY KEY (`feedback_id`),
  ADD KEY `customer_id` (`customer_id`);

--
-- Indexes for table `invoices`
--
ALTER TABLE `invoices`
  ADD PRIMARY KEY (`invoice_id`),
  ADD KEY `appointment_id` (`appointment_id`),
  ADD KEY `customer_id` (`customer_id`);

--
-- Indexes for table `job_cards`
--
ALTER TABLE `job_cards`
  ADD PRIMARY KEY (`job_card_id`),
  ADD KEY `appointment_id` (`appointment_id`),
  ADD KEY `technician_id` (`technician_id`);

--
-- Indexes for table `job_parts`
--
ALTER TABLE `job_parts`
  ADD PRIMARY KEY (`part_id`),
  ADD KEY `job_card_id` (`job_card_id`);

--
-- Indexes for table `services`
--
ALTER TABLE `services`
  ADD PRIMARY KEY (`service_id`);

--
-- Indexes for table `spare_parts`
--
ALTER TABLE `spare_parts`
  ADD PRIMARY KEY (`part_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `email` (`email`);

--
-- Indexes for table `vehicles`
--
ALTER TABLE `vehicles`
  ADD PRIMARY KEY (`vehicle_id`),
  ADD UNIQUE KEY `license_plate` (`license_plate`),
  ADD KEY `customer_id` (`customer_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `appointments`
--
ALTER TABLE `appointments`
  MODIFY `appointment_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `feedback`
--
ALTER TABLE `feedback`
  MODIFY `feedback_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `invoices`
--
ALTER TABLE `invoices`
  MODIFY `invoice_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `job_cards`
--
ALTER TABLE `job_cards`
  MODIFY `job_card_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- AUTO_INCREMENT for table `job_parts`
--
ALTER TABLE `job_parts`
  MODIFY `part_id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `services`
--
ALTER TABLE `services`
  MODIFY `service_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `spare_parts`
--
ALTER TABLE `spare_parts`
  MODIFY `part_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `vehicles`
--
ALTER TABLE `vehicles`
  MODIFY `vehicle_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=2;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `appointments`
--
ALTER TABLE `appointments`
  ADD CONSTRAINT `appointments_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `users` (`user_id`),
  ADD CONSTRAINT `appointments_ibfk_2` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`vehicle_id`);

--
-- Constraints for table `feedback`
--
ALTER TABLE `feedback`
  ADD CONSTRAINT `feedback_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `invoices`
--
ALTER TABLE `invoices`
  ADD CONSTRAINT `invoices_ibfk_1` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`appointment_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `invoices_ibfk_2` FOREIGN KEY (`customer_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;

--
-- Constraints for table `job_cards`
--
ALTER TABLE `job_cards`
  ADD CONSTRAINT `job_cards_ibfk_1` FOREIGN KEY (`appointment_id`) REFERENCES `appointments` (`appointment_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `job_cards_ibfk_2` FOREIGN KEY (`technician_id`) REFERENCES `users` (`user_id`) ON DELETE SET NULL;

--
-- Constraints for table `job_parts`
--
ALTER TABLE `job_parts`
  ADD CONSTRAINT `job_parts_ibfk_1` FOREIGN KEY (`job_card_id`) REFERENCES `job_cards` (`job_card_id`) ON DELETE CASCADE;

--
-- Constraints for table `vehicles`
--
ALTER TABLE `vehicles`
  ADD CONSTRAINT `vehicles_ibfk_1` FOREIGN KEY (`customer_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
