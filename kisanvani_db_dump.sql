-- =====================================================
-- Kisan Vani AI - MySQL Database Dump
-- Database: kisanvani_db
-- Based on Alembic Migration: 001_initial
-- Character Set: utf8mb4
-- Collation: utf8mb4_unicode_ci
-- =====================================================

-- Create Database
DROP DATABASE IF EXISTS kisanvani_db;
CREATE DATABASE kisanvani_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE kisanvani_db;

-- =====================================================
-- Table: alembic_version
-- =====================================================
DROP TABLE IF EXISTS `alembic_version`;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO `alembic_version` VALUES ('001_initial');

-- =====================================================
-- Table: users
-- =====================================================
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `email` varchar(200) DEFAULT NULL,
  `hashed_password` varchar(500) NOT NULL,
  `full_name` varchar(200) DEFAULT NULL,
  `role` varchar(50) DEFAULT 'operator',
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_users_username` (`username`),
  UNIQUE KEY `ix_users_email` (`email`),
  KEY `ix_users_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample admin user (password: admin123)
INSERT INTO `users` (`username`, `email`, `hashed_password`, `full_name`, `role`, `is_active`, `created_at`)
VALUES 
('admin', 'admin@kisanvani.com', '$2b$12$6ujOSqqxxAi5Rva0L3Orbu32jdchGVY8fzQK8FQm0li/7F1A0Us2q', 'Admin User', 'admin', 1, NOW());

-- =====================================================
-- Table: farmers
-- =====================================================
DROP TABLE IF EXISTS `farmers`;
CREATE TABLE `farmers` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `phone_number` varchar(15) NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `village` varchar(200) DEFAULT NULL,
  `district` varchar(200) DEFAULT NULL,
  `state` varchar(200) DEFAULT NULL,
  `crop_type` varchar(200) DEFAULT NULL,
  `land_size` varchar(50) DEFAULT NULL,
  `language` varchar(10) DEFAULT 'hi',
  `status` enum('ACTIVE','INACTIVE') DEFAULT 'ACTIVE',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_farmers_phone_number` (`phone_number`),
  KEY `ix_farmers_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample farmers
INSERT INTO `farmers` (`phone_number`, `name`, `village`, `district`, `state`, `crop_type`, `land_size`, `language`, `status`)
VALUES 
('+919876543210', 'राम सिंह', 'रामपुर', 'बिजनौर', 'उत्तर प्रदेश', 'wheat', '5 acres', 'hi', 'ACTIVE'),
('+919876543211', 'श्याम लाल', 'कमलापुर', 'मेरठ', 'उत्तर प्रदेश', 'rice', '3 acres', 'hi', 'ACTIVE');

-- =====================================================
-- Table: call_sessions
-- =====================================================
DROP TABLE IF EXISTS `call_sessions`;
CREATE TABLE `call_sessions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` varchar(100) NOT NULL,
  `farmer_id` int(11) DEFAULT NULL,
  `phone_number` varchar(15) NOT NULL,
  `provider_name` varchar(50) DEFAULT NULL,
  `provider_call_id` varchar(200) DEFAULT NULL,
  `status` enum('ACTIVE','COMPLETED','FAILED') DEFAULT 'ACTIVE',
  `start_time` datetime DEFAULT CURRENT_TIMESTAMP,
  `end_time` datetime DEFAULT NULL,
  `duration_seconds` int(11) DEFAULT 0,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `ix_call_sessions_session_id` (`session_id`),
  KEY `ix_call_sessions_id` (`id`),
  KEY `farmer_id` (`farmer_id`),
  CONSTRAINT `call_sessions_ibfk_1` FOREIGN KEY (`farmer_id`) REFERENCES `farmers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: cases
-- =====================================================
DROP TABLE IF EXISTS `cases`;
CREATE TABLE `cases` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `session_id` int(11) NOT NULL,
  `farmer_id` int(11) NOT NULL,
  `problem_text` text NOT NULL,
  `problem_category` varchar(100) DEFAULT NULL,
  `crop_name` varchar(100) DEFAULT NULL,
  `status` enum('OPEN','IN_PROGRESS','RESOLVED','ESCALATED') DEFAULT 'OPEN',
  `confidence_score` varchar(10) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_cases_id` (`id`),
  KEY `session_id` (`session_id`),
  KEY `farmer_id` (`farmer_id`),
  CONSTRAINT `cases_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `call_sessions` (`id`),
  CONSTRAINT `cases_ibfk_2` FOREIGN KEY (`farmer_id`) REFERENCES `farmers` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: advisories
-- =====================================================
DROP TABLE IF EXISTS `advisories`;
CREATE TABLE `advisories` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `case_id` int(11) NOT NULL,
  `advisory_text_hindi` text NOT NULL,
  `advisory_text_english` text DEFAULT NULL,
  `immediate_action` text DEFAULT NULL,
  `next_48_hours` text DEFAULT NULL,
  `preventive_measures` text DEFAULT NULL,
  `kb_entry_ids` text DEFAULT NULL,
  `was_escalated` tinyint(1) DEFAULT 0,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_advisories_id` (`id`),
  KEY `case_id` (`case_id`),
  CONSTRAINT `advisories_ibfk_1` FOREIGN KEY (`case_id`) REFERENCES `cases` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Table: kb_entries
-- =====================================================
DROP TABLE IF EXISTS `kb_entries`;
CREATE TABLE `kb_entries` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `title` varchar(500) NOT NULL,
  `content` text NOT NULL,
  `crop_name` varchar(100) DEFAULT NULL,
  `problem_type` varchar(100) DEFAULT NULL,
  `solution_steps` text DEFAULT NULL,
  `tags` text DEFAULT NULL,
  `is_approved` tinyint(1) DEFAULT 1,
  `is_banned` tinyint(1) DEFAULT 0,
  `language` varchar(10) DEFAULT 'hi',
  `created_by` varchar(100) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `ix_kb_entries_id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample Knowledge Base Entries (Hindi Agricultural Content)
INSERT INTO `kb_entries` (`title`, `content`, `crop_name`, `problem_type`, `solution_steps`, `tags`, `is_approved`, `is_banned`, `language`, `created_by`)
VALUES 
('गेहूं में पीले पत्ते - नाइट्रोजन की कमी', 
 'गेहूं की फसल में पीले पत्ते आना नाइट्रोजन की कमी का संकेत है। यह समस्या विशेष रूप से फसल की प्रारंभिक अवस्था में देखी जाती है। पुराने पत्ते पहले पीले होते हैं।', 
 'wheat', 
 'nutrient_deficiency', 
 '1. यूरिया 50 किलो प्रति एकड़ डालें\n2. पानी दें\n3. 7-10 दिन में सुधार दिखेगा', 
 'wheat,nitrogen,yellow_leaves,fertilizer', 
 1, 0, 'hi', 'system'),

('धान में भूरा धब्बा रोग', 
 'भूरा धब्बा रोग धान की फसल में फंगस के कारण होता है। पत्तियों पर भूरे रंग के धब्बे दिखाई देते हैं। यह रोग नमी और गर्म मौसम में तेजी से फैलता है।', 
 'rice', 
 'fungal_disease', 
 '1. कार्बेन्डाजिम स्प्रे करें\n2. खेत में जल निकासी सुधारें\n3. 15 दिन बाद दोबारा स्प्रे करें', 
 'rice,fungal,brown_spot,carbendazim', 
 1, 0, 'hi', 'system'),

('सोयाबीन में कीट प्रकोप - तना छेदक', 
 'तना छेदक कीट सोयाबीन के तने में छेद करके अंदर घुस जाता है। इससे पौधा कमजोर हो जाता है और उपज कम हो जाती है। पौधे का ऊपरी हिस्सा मुरझा सकता है।', 
 'soybean', 
 'pest_attack', 
 '1. क्लोरपायरीफॉस स्प्रे करें\n2. प्रभावित पौधों को हटा दें\n3. खेत की निगरानी रखें', 
 'soybean,pest,stem_borer,chlorpyrifos', 
 1, 0, 'hi', 'system'),

('कपास में सिंचाई की समस्या', 
 'कपास की फसल को पानी की सही मात्रा चाहिए। कम पानी से पौधे सूख जाते हैं और ज्यादा पानी से जड़ें सड़ सकती हैं। फूल आने के समय पर्याप्त पानी जरूरी है।', 
 'cotton', 
 'irrigation', 
 '1. 10-12 दिन में सिंचाई करें\n2. फूल आने पर नियमित पानी दें\n3. जल निकासी का ध्यान रखें', 
 'cotton,irrigation,water_management', 
 1, 0, 'hi', 'system'),

('मक्का में खाद प्रबंधन', 
 'मक्का की अच्छी पैदावार के लिए संतुलित खाद जरूरी है। एनपीके (नाइट्रोजन, फॉस्फोरस, पोटैशियम) सही अनुपात में डालना चाहिए।', 
 'maize', 
 'fertilization', 
 '1. बुवाई के समय DAP 50 किलो\n2. 30 दिन बाद यूरिया 25 किलो\n3. 45 दिन बाद यूरिया 25 किलो', 
 'maize,fertilizer,NPK,urea,DAP', 
 1, 0, 'hi', 'system');

-- =====================================================
-- Table: escalations
-- =====================================================
DROP TABLE IF EXISTS `escalations`;
CREATE TABLE `escalations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `case_id` int(11) NOT NULL,
  `reason` text NOT NULL,
  `confidence_score` varchar(10) DEFAULT NULL,
  `status` enum('PENDING','IN_REVIEW','RESOLVED','REJECTED') DEFAULT 'PENDING',
  `assigned_to` varchar(100) DEFAULT NULL,
  `resolution_notes` text DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `resolved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_escalations_id` (`id`),
  KEY `case_id` (`case_id`),
  CONSTRAINT `escalations_ibfk_1` FOREIGN KEY (`case_id`) REFERENCES `cases` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- =====================================================
-- Import Instructions
-- =====================================================
-- To import this database:
-- 
-- 1. Using MySQL/MariaDB command line:
--    mysql -u root -p < kisanvani_db_dump.sql
--
-- 2. Or create database first, then import:
--    mysql -u root -p
--    source /path/to/kisanvani_db_dump.sql
--
-- 3. Verify import:
--    mysql -u root -p kisanvani_db
--    SHOW TABLES;
--    SELECT COUNT(*) FROM kb_entries;
--
-- 4. Create user with proper permissions:
--    CREATE USER 'kisanvani'@'localhost' IDENTIFIED BY 'kisanvani2025';
--    GRANT ALL PRIVILEGES ON kisanvani_db.* TO 'kisanvani'@'localhost';
--    FLUSH PRIVILEGES;
--
-- =====================================================
-- Database Statistics
-- =====================================================
-- Tables: 8 (users, farmers, call_sessions, cases, advisories, kb_entries, escalations, alembic_version)
-- Sample Data: 1 admin user, 2 farmers, 5 KB entries
-- Character Set: UTF-8 (utf8mb4) for Hindi content support
-- Engine: InnoDB with foreign key constraints
-- =====================================================
