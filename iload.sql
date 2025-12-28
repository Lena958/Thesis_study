-- phpMyAdmin SQL Dump
-- version 5.2.0
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Nov 30, 2025 at 03:56 PM
-- Server version: 10.4.24-MariaDB
-- PHP Version: 8.1.6

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `iload`
--

-- --------------------------------------------------------

--
-- Table structure for table `conflicts`
--

CREATE TABLE `conflicts` (
  `conflict_id` int(11) NOT NULL,
  `schedule1_id` int(11) NOT NULL,
  `schedule2_id` int(11) NOT NULL,
  `conflict_type` varchar(50) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `recommendation` text DEFAULT NULL,
  `status` enum('Pending','Resolved') DEFAULT 'Pending'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `conflicts`
--

INSERT INTO `conflicts` (`conflict_id`, `schedule1_id`, `schedule2_id`, `conflict_type`, `description`, `recommendation`, `status`) VALUES
(1, 319, 385, 'Room Double Booking', 'Room 105 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Networking 2\' on Monday 07:00 AM - 08:00 AM and 07:00 AM - 08:00 AM', 'Move one of the classes to another available room or adjust the schedule.', 'Resolved'),
(2, 436, 322, 'Room Double Booking', 'Room 303 has overlapping classes: \'Cybersecurity\' and \'Applied Business Tools and Technologies\' on Monday 08:00 AM - 09:30 AM and 09:00 AM - 10:30 AM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(3, 322, 358, 'Room Double Booking', 'Room 303 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Programmable Control\' on Monday 09:00 AM - 10:30 AM and 10:00 AM - 11:30 AM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(4, 320, 386, 'Room Double Booking', 'Room 105 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Networking 2\' on Wednesday 07:00 AM - 08:00 AM and 07:00 AM - 08:00 AM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(5, 437, 323, 'Room Double Booking', 'Room 303 has overlapping classes: \'Cybersecurity\' and \'Applied Business Tools and Technologies\' on Wednesday 08:00 AM - 09:30 AM and 09:00 AM - 10:30 AM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(6, 323, 359, 'Room Double Booking', 'Room 303 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Programmable Control\' on Wednesday 09:00 AM - 10:30 AM and 10:00 AM - 11:30 AM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(7, 321, 387, 'Room Double Booking', 'Room 105 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Networking 2\' on Friday 07:00 AM - 08:00 AM and 07:00 AM - 08:00 AM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(8, 438, 324, 'Room Double Booking', 'Room 303 has overlapping classes: \'Cybersecurity\' and \'Applied Business Tools and Technologies\' on Friday 08:00 AM - 09:30 AM and 09:00 AM - 10:30 AM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(9, 324, 360, 'Room Double Booking', 'Room 303 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Programmable Control\' on Friday 09:00 AM - 10:30 AM and 10:00 AM - 11:30 AM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(10, 1246, 1311, 'Room Double Booking', 'Room 106 has overlapping classes: \'None\' and \'Web Systems and Technologies\' on Monday 02:00 PM - 03:00 PM and 02:30 PM - 03:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(11, 1247, 1312, 'Room Double Booking', 'Room 106 has overlapping classes: \'None\' and \'Web Systems and Technologies\' on Wednesday 02:00 PM - 03:00 PM and 02:30 PM - 03:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(12, 1248, 1313, 'Room Double Booking', 'Room 106 has overlapping classes: \'None\' and \'Web Systems and Technologies\' on Friday 02:00 PM - 03:00 PM and 02:30 PM - 03:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(13, 1366, 1246, 'Room Double Booking', 'Room 106 has overlapping classes: \'Applied Business Tools and Technologies\' and \'None\' on Monday 01:30 PM - 02:30 PM and 02:00 PM - 03:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(14, 1367, 1247, 'Room Double Booking', 'Room 106 has overlapping classes: \'Applied Business Tools and Technologies\' and \'None\' on Wednesday 01:30 PM - 02:30 PM and 02:00 PM - 03:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(15, 1368, 1248, 'Room Double Booking', 'Room 106 has overlapping classes: \'Applied Business Tools and Technologies\' and \'None\' on Friday 01:30 PM - 02:30 PM and 02:00 PM - 03:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(16, 184, 262, 'Room Double Booking', 'Room 106 has overlapping classes: \'Purposive Communication\' and \'Web Systems and Technologies\' on Monday 01:30 PM - 02:30 PM and 01:30 PM - 02:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(17, 185, 263, 'Room Double Booking', 'Room 106 has overlapping classes: \'Purposive Communication\' and \'Web Systems and Technologies\' on Wednesday 01:30 PM - 02:30 PM and 01:30 PM - 02:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(18, 264, 186, 'Room Double Booking', 'Room 106 has overlapping classes: \'Web Systems and Technologies\' and \'Purposive Communication\' on Friday 01:30 PM - 02:30 PM and 01:30 PM - 02:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(19, 317, 184, 'Room Double Booking', 'Room 106 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Purposive Communication\' on Monday 01:00 PM - 02:00 PM and 01:30 PM - 02:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(20, 318, 185, 'Room Double Booking', 'Room 106 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Purposive Communication\' on Wednesday 01:00 PM - 02:00 PM and 01:30 PM - 02:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(21, 319, 186, 'Room Double Booking', 'Room 106 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Purposive Communication\' on Friday 01:00 PM - 02:00 PM and 01:30 PM - 02:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(22, 590, 650, 'Room Double Booking', 'Room 303 has overlapping classes: \'Computer Programming\' and \'Living in IT Era\' on Tuesday 12:30 PM - 02:00 PM and 01:30 PM - 03:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(23, 585, 620, 'Room Double Booking', 'Room 302 has overlapping classes: \'Computer Programming\' and \'Applied Business Tools and Technologies\' on Tuesday 05:00 PM - 06:30 PM and 05:30 PM - 07:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(24, 591, 651, 'Room Double Booking', 'Room 303 has overlapping classes: \'Computer Programming\' and \'Living in IT Era\' on Thursday 12:30 PM - 02:00 PM and 01:30 PM - 03:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(25, 586, 621, 'Room Double Booking', 'Room 302 has overlapping classes: \'Computer Programming\' and \'Applied Business Tools and Technologies\' on Thursday 05:00 PM - 06:30 PM and 05:30 PM - 07:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(26, 680, 590, 'Room Double Booking', 'Room 303 has overlapping classes: \'Web Systems and Technologies\' and \'Computer Programming\' on Tuesday 12:00 PM - 01:30 PM and 12:30 PM - 02:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(27, 675, 585, 'Room Double Booking', 'Room 302 has overlapping classes: \'Technopeneurship\' and \'Computer Programming\' on Tuesday 04:30 PM - 06:00 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(28, 681, 591, 'Room Double Booking', 'Room 303 has overlapping classes: \'Web Systems and Technologies\' and \'Computer Programming\' on Thursday 12:00 PM - 01:30 PM and 12:30 PM - 02:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(29, 676, 586, 'Room Double Booking', 'Room 302 has overlapping classes: \'Technopeneurship\' and \'Computer Programming\' on Thursday 04:30 PM - 06:00 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(30, 590, 750, 'Room Double Booking', 'Room 303 has overlapping classes: \'Computer Programming\' and \'Applied Business Tools and Technologies\' on Tuesday 12:30 PM - 02:00 PM and 12:30 PM - 02:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(31, 751, 591, 'Room Double Booking', 'Room 303 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Computer Programming\' on Thursday 12:30 PM - 02:00 PM and 12:30 PM - 02:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(32, 800, 585, 'Room Double Booking', 'Room 302 has overlapping classes: \'Technopeneurship\' and \'Computer Programming\' on Tuesday 05:00 PM - 06:30 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(33, 801, 586, 'Room Double Booking', 'Room 302 has overlapping classes: \'Technopeneurship\' and \'Computer Programming\' on Thursday 05:00 PM - 06:30 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(34, 815, 590, 'Room Double Booking', 'Room 303 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Computer Programming\' on Tuesday 12:00 PM - 01:30 PM and 12:30 PM - 02:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(35, 816, 591, 'Room Double Booking', 'Room 303 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Computer Programming\' on Thursday 12:00 PM - 01:30 PM and 12:30 PM - 02:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(36, 590, 880, 'Room Double Booking', 'Room 303 has overlapping classes: \'Computer Programming\' and \'Web Systems and Technologies\' on Tuesday 12:30 PM - 02:00 PM and 01:00 PM - 02:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(37, 870, 585, 'Room Double Booking', 'Room 302 has overlapping classes: \'Technopeneurship\' and \'Computer Programming\' on Tuesday 04:30 PM - 06:00 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(38, 591, 881, 'Room Double Booking', 'Room 303 has overlapping classes: \'Computer Programming\' and \'Web Systems and Technologies\' on Thursday 12:30 PM - 02:00 PM and 01:00 PM - 02:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(39, 871, 586, 'Room Double Booking', 'Room 302 has overlapping classes: \'Technopeneurship\' and \'Computer Programming\' on Thursday 04:30 PM - 06:00 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(40, 915, 590, 'Room Double Booking', 'Room 303 has overlapping classes: \'Web Systems and Technologies\' and \'Computer Programming\' on Tuesday 12:30 PM - 02:00 PM and 12:30 PM - 02:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(41, 585, 930, 'Room Double Booking', 'Room 302 has overlapping classes: \'Computer Programming\' and \'Applied Business Tools and Technologies\' on Tuesday 05:00 PM - 06:30 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(42, 916, 591, 'Room Double Booking', 'Room 303 has overlapping classes: \'Web Systems and Technologies\' and \'Computer Programming\' on Thursday 12:30 PM - 02:00 PM and 12:30 PM - 02:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(43, 931, 586, 'Room Double Booking', 'Room 302 has overlapping classes: \'Applied Business Tools and Technologies\' and \'Computer Programming\' on Thursday 05:00 PM - 06:30 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(44, 585, 1005, 'Room Double Booking', 'Room 302 has overlapping classes: \'Computer Programming\' and \'Applied Business Tools and Technologies\' on Tuesday 05:00 PM - 06:30 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(45, 586, 1006, 'Room Double Booking', 'Room 302 has overlapping classes: \'Computer Programming\' and \'Applied Business Tools and Technologies\' on Thursday 05:00 PM - 06:30 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(46, 590, 1045, 'Room Double Booking', 'Room 303 has overlapping classes: \'Computer Programming\' and \'Living in IT Era\' on Tuesday 12:30 PM - 02:00 PM and 01:30 PM - 03:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(47, 1010, 585, 'Room Double Booking', 'Room 302 has overlapping classes: \'Web Systems and Technologies\' and \'Computer Programming\' on Tuesday 05:00 PM - 06:30 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(48, 591, 1046, 'Room Double Booking', 'Room 303 has overlapping classes: \'Computer Programming\' and \'Living in IT Era\' on Thursday 12:30 PM - 02:00 PM and 01:30 PM - 03:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(49, 586, 1011, 'Room Double Booking', 'Room 302 has overlapping classes: \'Computer Programming\' and \'Web Systems and Technologies\' on Thursday 05:00 PM - 06:30 PM and 05:00 PM - 06:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(50, 590, 1070, 'Room Double Booking', 'Room 303 has overlapping classes: \'Computer Programming\' and \'Programmable Control\' on Tuesday 12:30 PM - 02:00 PM and 01:00 PM - 02:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(51, 585, 1085, 'Room Double Booking', 'Room 302 has overlapping classes: \'Computer Programming\' and \'Technopeneurship\' on Tuesday 05:00 PM - 06:30 PM and 05:30 PM - 07:00 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(52, 591, 1071, 'Room Double Booking', 'Room 303 has overlapping classes: \'Computer Programming\' and \'Programmable Control\' on Thursday 12:30 PM - 02:00 PM and 01:00 PM - 02:30 PM', 'Move one of the classes to another available room or adjust the schedule.', ''),
(53, 586, 1086, 'Room Double Booking', 'Room 302 has overlapping classes: \'Computer Programming\' and \'Technopeneurship\' on Thursday 05:00 PM - 06:30 PM and 05:30 PM - 07:00 PM', 'Move one of the classes to another available room or adjust the schedule.', '');

-- --------------------------------------------------------

--
-- Table structure for table `courses`
--

CREATE TABLE `courses` (
  `course_id` int(11) NOT NULL,
  `course_code` varchar(20) NOT NULL,
  `course_name` varchar(100) NOT NULL,
  `school_year` varchar(9) NOT NULL,
  `semester` enum('First Semester','Second Semester','Summer') NOT NULL,
  `program` varchar(100) NOT NULL,
  `course_type` enum('Major','GEC','GEE') DEFAULT 'Major'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `courses`
--

INSERT INTO `courses` (`course_id`, `course_code`, `course_name`, `school_year`, `semester`, `program`, `course_type`) VALUES
(1, 'INDTCH 5', 'Programmable Control', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(6, 'ITCHI 1', 'Computer Human Interaction', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(7, 'INFOT 5', 'Networking 2', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(8, 'ICTAP 2', 'Applied Business Tools and Technologies', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(9, 'INFOT 2', 'Web Systems and Technologies', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(10, 'CPROG 1', 'Computer Programming', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(11, 'DSTRU 1', 'Data Structures and Algorithms', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(12, 'INFOT 4', 'Quantitative Methods', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(13, 'INFOE 1', 'Introduction to Cryptography', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(14, 'INFOE 2', 'Cybersecurity', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(15, 'INFOE 5', 'Effective Interfaces Development', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(18, 'INFOE 6', 'Networks and Security', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(19, 'ITCOM 1', 'Introduction to Computing', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(20, 'TPREN 1', 'Technopeneurship', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(22, 'GEE 22', 'Living in IT Era', '2025-2026', 'First Semester', 'BSIT', 'Major'),
(23, 'GEE 2', 'Purposive Communication', '2025-2026', 'First Semester', 'BSIT', 'GEE');

-- --------------------------------------------------------

--
-- Table structure for table `instructors`
--

CREATE TABLE `instructors` (
  `instructor_id` int(10) UNSIGNED NOT NULL,
  `name` varchar(100) NOT NULL,
  `max_load_units` int(11) NOT NULL,
  `department` varchar(100) DEFAULT NULL,
  `program` varchar(100) DEFAULT NULL,
  `status` varchar(50) DEFAULT NULL,
  `username` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `role` enum('admin','instructor') DEFAULT 'instructor',
  `image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `instructors`
--

INSERT INTO `instructors` (`instructor_id`, `name`, `max_load_units`, `department`, `program`, `status`, `username`, `password`, `role`, `image`) VALUES
(1, 'Juan Dela Cruz', 26, 'College of Computing and Information Sciences', 'BSCS', 'Permanent', 'admin1', 'scrypt:32768:8:1$M0a8Q9jplx7MJWCI$ef8dab5827ab340dadb02c8fc81b421d9b2e7a5dd16829d7f28ce56ac6fc8510452db6811d842843e618829ec5609c24992f7a15dec9d9e50c9d9684e9496aaa', 'admin', 'bonappetit.png'),
(2, 'Lyda Magtalas', 25, 'College of Computing and Information Sciences', 'BSIT', 'Permanent', 'admin2', 'scrypt:32768:8:1$uec28SPvVikaY47v$742b6a70f27b43d23e42364c48e7677bd6e5eeec5a5f228016bf35ec76bc014dd06a7406bd1e3fe9fffa3224e1cf790fe611623882654d423924b12f3e008831', 'admin', 'face6.jpg'),
(8, 'Terrence Calatrava', 22, 'College of Computing and Information Sciences', 'BSIT', 'Part Time', 't.calatrava', 'scrypt:32768:8:1$QL5RMdHJfeejYs83$469a14c68ed9bc896bab4c2712b283a17becc3d789b315fc4556d348edb75d84b3da1f4ec119037bc47d598775646e76dffe2d89b932940404272d23d37fc4d4', 'instructor', NULL),
(9, 'Roman Romulo', 25, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'rromulo.25', 'scrypt:32768:8:1$Zi9eOOSAcLt63try$48389878e0c6fb4931784ec9b9ed79a33d39dc69d24bcc276b24a166c11d968a8cb7eaffa2d38e74d14e8436d0050a1049c041a98086b908ae0250167dc5b703', 'instructor', NULL),
(10, 'Jojo Ang', 24, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'J.Ang', 'scrypt:32768:8:1$VJoRjPENSeVSBcZd$1cacb9b8f13ab20694c529e8ab35878a329285d7afbed6c57622fbd877febf00fa8d2b193f47470106899b5fc7ac89eaf2d6f377274e195c41f90f65b0ead481', 'instructor', NULL),
(11, 'Patrick Michael Vargas', 25, 'College of Computing and Information Sciences', 'BSIT', 'Part Time', 'PMVargas', 'scrypt:32768:8:1$ctw4MvhmvM1PxpVi$88255c52d296f7350c500c4ca31b4356d1a8586c4c942c51d3333e1b9c6e5ebcdc914901da60dfdf4fad8e51c0fd50f1e5c17386e485a5d4354c5eb6f5fbeeb0', 'instructor', NULL),
(13, 'Nikki Briones', 22, 'College of Computing and Information Sciences', 'BSIT', 'Part Time', 'NiksB', 'scrypt:32768:8:1$SQjj19o4yMOBPuR6$33b2c3d6d3017997ddfa22cc9681d9ade1c4013e7ed1c87d28c9cf85c87f5b9a858df2aa29f24ce76c5a96402f834581a7768d939dbd689e41df724988fd5070', 'instructor', NULL),
(14, 'Marcelino Teodoro', 25, 'College of Computing and Information Sciences', 'BSIT', 'Part Time', 'MTeodoro', 'scrypt:32768:8:1$hHF0B5v6t8ImYwWg$cb100bb604a96ab98f5a2e87bf9a429f75eafb70fbfbad39d442085f539065ac00d889499b13d3ab5f91e562979ba52753477dea907a1831a6c4115ee4e0cf54', 'instructor', NULL),
(15, 'Florida Robes', 25, 'College of Computing and Information Sciences', 'BSIT', 'Part Time', 'FlorRobes', 'scrypt:32768:8:1$foqbimT2O9xhkcuu$41f85a6c39bb03ae687a1c92bcec3bc522f94052474f0f06cf0a4a23f18cdf17bc06c1af498393cb95aff086ab8603cab9eddbca720e9d0fd49c3a170e3c6188', 'instructor', NULL),
(16, 'Eleandro Madrona', 22, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'ElMadrona', 'scrypt:32768:8:1$sbX9pvzibksvzEex$3d9a5bd1dc713872bd1de48152a14582482d6a4741ed4c73995cd25bdd52c84bec915f853d01d675afa43c40f3b765cc3f47b1a680efd67804a2b7f6dc525208', 'instructor', NULL),
(17, 'Benjamin Agarao Jr.', 24, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'JrAgarao', 'scrypt:32768:8:1$XFPx88nEqOOURixY$6166dadff7449d6b9bcfe976b52b3ee5b79b94a6ec3e466957693857ebf05cff3ec6a4e8b0ef5771beb3186e1e4f69f9ffdcd5a48b66097f808f2a1cee26fc02', 'instructor', NULL),
(18, 'Florencio Gabriel Noel', 22, 'College of Computing and Information Sciences', 'BSIT', 'Permanent', 'FGabriel', 'scrypt:32768:8:1$kIc6AqakmSC3eIdD$8c9258c863f2646216b0c5c0554791face2857a0723dec052b41b49fc8cc5558e06b30fca68b1bdcbde7dcd42ab17edff4f585cc1f9ace2f214c1f265b0deb69', 'instructor', NULL),
(19, 'Leody Tarriela', 25, 'College of Computing and Information Sciences', 'BSIT', 'Part Time', 'LTarriela', 'scrypt:32768:8:1$3DyUXbxJnO6poqfu$7e3255099a73d5c1a5639cf9a877a058da4c0b0e1e8a84e649c6f579b9c3dca1986c12e3ddf14ddfad20927fb41370846a628797d46227027b40c090b053ee56', 'instructor', NULL),
(20, 'Reynante Arogancia', 25, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'R.Arogancia', 'scrypt:32768:8:1$Ty9tC8tmMeeODjar$8f7e381b27b78beefb550d868960cb12d5ccc4fa19d97b144ea53cf3cd2401470d410c90f927e26e3ad63d3f45fd5d2e3ca0ec95d229e3dda1b8e2c953156909', 'instructor', NULL),
(21, 'Marvin Rillo', 22, 'College of Computing and Information Sciences', 'BSIT', 'Part Time', 'MaRillo', 'scrypt:32768:8:1$CRBqp7tsGNt39QH2$f24acd355ac5ed1cab8dc8ad6de274264f356b64c4b5824aa54feb30aa4b5e04c22ad3b8457c22a5e6122bf35cfc148394c10bb21fec35a0b310fc33f2aa98a3', 'instructor', NULL),
(22, 'Teodorico Haresco Jr.', 22, 'College of Computing and Information Sciences', 'BSIT', 'Part Time', 'TDHaresco', 'scrypt:32768:8:1$4JBDwDUZOzntrQNq$ef29ab5508108a77e6e76756295a36559c52a8ec4cf5931fee8a303b4e3a353e5a2f3ef05f8dc8d2856252baa26d4f7caf45c3306c3d8bf4dd35665c8cd5d15f', 'instructor', NULL),
(23, 'Antonieta Eudela', 22, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'Eudela', 'scrypt:32768:8:1$BwXH6RLxDnxHGUbC$5737ee70d5ac08d790c493d24fad0f58afcb5aca9a9dd05c54702518bfb7c1179cc7b06bab05adb30b64e5e5a9b11a7d626c28b569448f7f4414b3cf586ff6da', 'instructor', NULL),
(24, 'Dean Asistio', 22, 'College of Computing and Information Sciences', 'BSCS', 'Permanent', 'DAsistio', 'scrypt:32768:8:1$a7E0Wra9xULjizjs$4019ffe85c8e6fef93d33293efe0ac47f5fdb269f6aeab963ab000e26ee5a26b2a6dbb68d3dba06282c024f6eb9cd0ec0926332114d5f28ea7f7aea4a703f1bf', 'instructor', NULL),
(25, 'Marivic Co Pillar', 22, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'MCopil', 'scrypt:32768:8:1$MTtK9RkYqHqOVtlK$8d7aa4e535392ae89b6bba96ef978ad600c24be2394695c0e95d04a82019cdee58f675e45a1fa5025871f18d35a4a7f42f4e2df59b137e7d4b459bb8c85dbdf0', 'instructor', NULL),
(26, 'Eduarte Virgilio', 24, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'EVirgilio', 'scrypt:32768:8:1$qbzTmAM1BQsArPBP$5fbbefeb272a1d551c20df1f2d1e04e888461a8e65464c32158b18632ceacca678ace07e647205a62880d700ab0da3dec37e6d136efd15db358860315800f974', 'instructor', NULL),
(27, 'Ramon Arriola', 24, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'Arriola', 'scrypt:32768:8:1$a0H9YJfJYQeen3f1$07d1f5663ecdadc875d0cd7634a19804cb89c45154ea2dc564f132b5b6bef4495f9bbcb3d493b1d9aad6f4af44d329213cb33bd270784707c85194a6d894bf47', 'instructor', NULL),
(28, 'Henry Alcantara', 24, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'HenTara', 'scrypt:32768:8:1$b4KSAPZcyuape1UF$e41a3b20e5a75de726068079f9f7089706aac1bd2a58da293a734c04766eff8507390c17b9a91f0497b8d289218def3adcafd116121090a209e18c50218a3e9c', 'instructor', NULL),
(29, 'Robert Bernardo', 24, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'Robernardo', 'scrypt:32768:8:1$4X7Qd7V6cBniz6M6$efe5f728808e8577d6d229526e176400db18bef7ba136e2d8cb2d9090f91cbd361d9f33c7ff4961f0983db4a02a2eb406867f0dba0c2a9011e17d4459455fb74', 'instructor', NULL),
(30, 'Aristotle Ramos', 24, 'College of Computing and Information Sciences', 'BSIT', 'Part Time', 'AristotleR', 'scrypt:32768:8:1$yutyVGgOUSRJSV4K$44c45eb5231ea04abe42e49be44295a03df45ffdc74dc5df9c5c8f3c2d272eb0aa25b3a29ec7a33e24aef59fb15043757fdf3617a8d97ff18db63efd3201295a', 'instructor', NULL),
(31, 'Manny Bulusan', 24, 'College of Computing and Information Sciences', 'BSCS', 'Permanent', 'MBulusan', 'scrypt:32768:8:1$yZGDIAxN89Jf7W5E$1c1843beb29f168788a191603e0cdf4eda4e957ee19a2b3b5684df1691634b27a036b46e1c87b18fcb38e8c8769c3e057129aafa2a2f1370eea2eaa46d3b9f00', 'instructor', NULL),
(32, 'Edgardo Pingol', 25, 'College of Computing and Information Sciences', 'BSIT', 'Permanent', 'EdPingol', 'scrypt:32768:8:1$H23WuzshkY9HbNtv$ffa0a0fcba3d1c29215518b8eb09e83b7ed9e88028a8aadbec7bd852c557f4e076dab1956b472ed895bd8d8d2ff8e95edaa1c7daac6c9ad75328b048f2a240a7', 'instructor', NULL),
(33, 'Zaldy Co', 25, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'ZCo', 'scrypt:32768:8:1$fRwWhIyxfCdWsmWh$cadd99e86df8f726f2d93fdabfd23cbbf625f57e84b7e42dcb721ec72e7bf83cd48d8674076f39b8e9fc81c5bf41f388c7074a5c53761c3e23d3f74a74810566', 'instructor', 'face16.jpg'),
(34, 'Arjo Atayde', 22, 'College of Computing and Information Sciences', 'BSCS', 'Part Time', 'Arjtayde', 'scrypt:32768:8:1$X3JGXgvd8A1q6fkq$e692497491ecc93fbad903aa7dbccb7070c74d0838f9de4495bc4449172068f963a080c1c0065a9c9b777523f0a752e56162e454948b95243cb19519bf27c5f7', 'instructor', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `rooms`
--

CREATE TABLE `rooms` (
  `room_id` int(11) NOT NULL,
  `room_number` varchar(20) NOT NULL,
  `room_type` enum('Lecture','Lab') NOT NULL,
  `image` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `rooms`
--

INSERT INTO `rooms` (`room_id`, `room_number`, `room_type`, `image`) VALUES
(30, '101', 'Lecture', NULL),
(31, '102', 'Lecture', NULL),
(32, '103', 'Lecture', NULL),
(33, '104', 'Lecture', NULL),
(34, '105', 'Lecture', NULL),
(35, '106', 'Lecture', NULL),
(36, '107', 'Lecture', NULL),
(37, '108', 'Lecture', NULL),
(38, '201', 'Lecture', NULL),
(39, '301', 'Lab', NULL),
(40, '302', 'Lab', NULL),
(41, '303', 'Lab', NULL),
(42, '304', 'Lab', NULL),
(43, '305', 'Lab', NULL),
(44, '306', 'Lab', NULL),
(45, '307', 'Lab', NULL),
(46, '308', 'Lab', NULL),
(47, '309', 'Lab', NULL);

-- --------------------------------------------------------

--
-- Table structure for table `room_availability`
--

CREATE TABLE `room_availability` (
  `id` int(11) NOT NULL,
  `room_id` int(11) DEFAULT NULL,
  `day_of_week` enum('Monday','Tuesday','Wednesday','Thursday','Friday') DEFAULT NULL,
  `start_time` time DEFAULT NULL,
  `end_time` time DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- --------------------------------------------------------

--
-- Table structure for table `room_feedback`
--

CREATE TABLE `room_feedback` (
  `feedback_id` int(11) NOT NULL,
  `room_id` int(11) NOT NULL,
  `rating` enum('Satisfied','Unsatisfied') DEFAULT NULL,
  `instructor_id` int(11) NOT NULL,
  `comments` text DEFAULT NULL,
  `feedback_date` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `room_feedback`
--

INSERT INTO `room_feedback` (`feedback_id`, `room_id`, `rating`, `instructor_id`, `comments`, `feedback_date`) VALUES
(9, 23, 'Satisfied', 33, 'guba bintana', '2025-09-20 14:22:52'),
(10, 14, 'Satisfied', 33, 'HAAHAHA', '2025-09-28 07:23:29');

-- --------------------------------------------------------

--
-- Table structure for table `room_programs`
--

CREATE TABLE `room_programs` (
  `room_id` int(11) NOT NULL,
  `program_name` varchar(255) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `room_programs`
--

INSERT INTO `room_programs` (`room_id`, `program_name`) VALUES
(30, 'GEN ED'),
(31, 'GEN ED'),
(32, 'GEN ED'),
(33, 'GEN ED'),
(34, 'GEN ED'),
(35, 'BSCS'),
(35, 'BSIT'),
(36, 'GEN ED'),
(37, 'BSIT'),
(38, 'BSCS'),
(39, 'BLIS'),
(40, 'BSCS'),
(40, 'BSIT'),
(41, 'BSCS'),
(41, 'BSIT'),
(42, 'BSCS'),
(42, 'BSIT'),
(43, 'BSCS'),
(44, 'BSCS'),
(44, 'BSIT'),
(45, 'BSCS'),
(45, 'BSIT'),
(46, 'BSCS'),
(47, 'BLIS'),
(47, 'BSCS'),
(47, 'BSIT');

-- --------------------------------------------------------

--
-- Table structure for table `schedules`
--

CREATE TABLE `schedules` (
  `schedule_id` int(11) NOT NULL,
  `subject_id` int(11) NOT NULL,
  `instructor_id` int(11) NOT NULL,
  `room_id` int(11) NOT NULL,
  `day_of_week` enum('Monday','Tuesday','Wednesday','Thursday','Friday') DEFAULT NULL,
  `start_time` time DEFAULT NULL,
  `end_time` time DEFAULT NULL,
  `semester` varchar(50) NOT NULL,
  `school_year` varchar(20) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp(),
  `approved` tinyint(1) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `schedules`
--

INSERT INTO `schedules` (`schedule_id`, `subject_id`, `instructor_id`, `room_id`, `day_of_week`, `start_time`, `end_time`, `semester`, `school_year`, `created_at`, `approved`) VALUES
(184, 22, 32, 35, 'Monday', '13:30:00', '14:30:00', 'First Semester', '2025-2026', '2025-11-30 00:53:40', 1),
(185, 22, 32, 35, 'Wednesday', '13:30:00', '14:30:00', 'First Semester', '2025-2026', '2025-11-30 00:53:40', 1),
(186, 22, 32, 35, 'Friday', '13:30:00', '14:30:00', 'First Semester', '2025-2026', '2025-11-30 00:53:40', 1),
(582, 9, 14, 35, 'Monday', '18:00:00', '19:00:00', 'First Semester', '2025-2026', '2025-11-30 01:07:13', 0),
(583, 9, 14, 35, 'Wednesday', '18:00:00', '19:00:00', 'First Semester', '2025-2026', '2025-11-30 01:07:13', 0),
(584, 9, 14, 35, 'Friday', '18:00:00', '19:00:00', 'First Semester', '2025-2026', '2025-11-30 01:07:13', 1),
(585, 9, 14, 40, 'Tuesday', '17:00:00', '18:30:00', 'First Semester', '2025-2026', '2025-11-30 01:07:13', 0),
(586, 9, 14, 40, 'Thursday', '17:00:00', '18:30:00', 'First Semester', '2025-2026', '2025-11-30 01:07:13', 0),
(587, 8, 14, 37, 'Monday', '17:00:00', '18:00:00', 'First Semester', '2025-2026', '2025-11-30 01:07:13', 0),
(588, 8, 14, 37, 'Wednesday', '17:00:00', '18:00:00', 'First Semester', '2025-2026', '2025-11-30 01:07:13', 0),
(589, 8, 14, 37, 'Friday', '17:00:00', '18:00:00', 'First Semester', '2025-2026', '2025-11-30 01:07:13', 1),
(590, 8, 14, 41, 'Tuesday', '12:30:00', '14:00:00', 'First Semester', '2025-2026', '2025-11-30 01:07:13', 0),
(591, 8, 14, 41, 'Thursday', '12:30:00', '14:00:00', 'First Semester', '2025-2026', '2025-11-30 01:07:13', 0),
(1057, 2, 2, 37, 'Monday', '11:00:00', '12:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1058, 2, 2, 37, 'Wednesday', '11:00:00', '12:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1059, 2, 2, 37, 'Friday', '11:00:00', '12:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1060, 2, 2, 41, 'Tuesday', '10:30:00', '12:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1061, 2, 2, 41, 'Thursday', '10:30:00', '12:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1062, 19, 2, 37, 'Monday', '16:00:00', '17:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1063, 19, 2, 37, 'Wednesday', '16:00:00', '17:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1064, 19, 2, 37, 'Friday', '16:00:00', '17:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1065, 19, 2, 41, 'Tuesday', '15:30:00', '17:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1066, 19, 2, 41, 'Thursday', '15:30:00', '17:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1067, 1, 2, 37, 'Monday', '09:30:00', '10:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1068, 1, 2, 37, 'Wednesday', '09:30:00', '10:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1069, 1, 2, 37, 'Friday', '09:30:00', '10:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1070, 1, 2, 41, 'Tuesday', '13:00:00', '14:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1071, 1, 2, 41, 'Thursday', '13:00:00', '14:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1072, 3, 8, 35, 'Monday', '17:00:00', '18:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1073, 3, 8, 35, 'Wednesday', '17:00:00', '18:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1074, 3, 8, 35, 'Friday', '17:00:00', '18:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1075, 3, 8, 40, 'Tuesday', '09:30:00', '11:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1076, 3, 8, 40, 'Thursday', '09:30:00', '11:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1077, 4, 8, 35, 'Monday', '12:30:00', '13:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1078, 4, 8, 35, 'Wednesday', '12:30:00', '13:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1079, 4, 8, 35, 'Friday', '12:30:00', '13:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1080, 4, 8, 40, 'Tuesday', '13:00:00', '14:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1081, 4, 8, 40, 'Thursday', '13:00:00', '14:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1082, 20, 15, 37, 'Monday', '12:30:00', '13:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1083, 20, 15, 37, 'Wednesday', '12:30:00', '13:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1084, 20, 15, 37, 'Friday', '12:30:00', '13:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1085, 20, 15, 40, 'Tuesday', '17:30:00', '19:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1086, 20, 15, 40, 'Thursday', '17:30:00', '19:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1087, 5, 11, 37, 'Monday', '14:00:00', '15:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1088, 5, 11, 37, 'Wednesday', '14:00:00', '15:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1089, 5, 11, 37, 'Friday', '14:00:00', '15:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1090, 5, 11, 40, 'Tuesday', '15:30:00', '17:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1091, 5, 11, 40, 'Thursday', '15:30:00', '17:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1092, 21, 15, 35, 'Monday', '07:30:00', '08:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1093, 21, 15, 35, 'Wednesday', '07:30:00', '08:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1094, 21, 15, 35, 'Friday', '07:30:00', '08:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1095, 21, 15, 42, 'Tuesday', '09:30:00', '11:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1096, 21, 15, 42, 'Thursday', '09:30:00', '11:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1097, 6, 13, 37, 'Monday', '08:30:00', '09:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1098, 6, 13, 37, 'Wednesday', '08:30:00', '09:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1099, 6, 13, 37, 'Friday', '08:30:00', '09:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1100, 6, 13, 42, 'Tuesday', '08:00:00', '09:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1101, 6, 13, 42, 'Thursday', '08:00:00', '09:30:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1102, 7, 13, 37, 'Monday', '18:00:00', '19:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1103, 7, 13, 37, 'Wednesday', '18:00:00', '19:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1104, 7, 13, 37, 'Friday', '18:00:00', '19:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1105, 7, 13, 40, 'Tuesday', '11:30:00', '13:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0),
(1106, 7, 13, 40, 'Thursday', '11:30:00', '13:00:00', 'First Semester', '2025-2026', '2025-11-30 16:09:19', 0);

-- --------------------------------------------------------

--
-- Table structure for table `subjects`
--

CREATE TABLE `subjects` (
  `subject_id` int(11) NOT NULL,
  `code` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `units` int(11) NOT NULL,
  `year_level` varchar(20) DEFAULT NULL,
  `section` varchar(20) NOT NULL,
  `instructor_id` int(11) DEFAULT NULL,
  `course` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Dumping data for table `subjects`
--

INSERT INTO `subjects` (`subject_id`, `code`, `name`, `units`, `year_level`, `section`, `instructor_id`, `course`) VALUES
(1, 'INDTCH 5', 'Programmable Control', 3, '2', 'B', 2, 'BSIT'),
(2, 'ITCHI 1', 'Computer Human Interaction', 3, '3', 'A', 2, 'BSIT'),
(3, 'INFOT 5', 'Networking 2', 3, '3', 'A', 8, 'BSIT'),
(4, 'ICTAP 2', 'Applied Business Tools and Technologies', 3, '4', 'A', 8, 'BSIT'),
(5, 'ICTAP 2', 'Applied Business Tools and Technologies', 3, '4', 'B', 11, 'BSIT'),
(6, 'INFOT 2', 'Web Systems and Technologies', 3, '3', 'A', 13, 'BSIT'),
(7, 'INFOT 2', 'Web Systems and Technologies', 3, '3', 'C', 13, 'BSIT'),
(8, 'CPROG 1', 'Computer Programming', 3, '1', 'A', 14, 'BSIT'),
(9, 'CPROG 1', 'Computer Programming', 3, '1', 'B', 14, 'BSIT'),
(19, 'GEE 22', 'Living in IT Era', 3, '1', 'B', 2, 'BSIT'),
(20, 'TPREN 1', 'Technopeneurship', 3, '2', 'A', 15, 'BSIT'),
(21, 'TPREN 1', 'Technopeneurship', 3, '2', 'B', 15, 'BSIT'),
(22, 'GEE 2', 'Purposive Communication', 3, '2', 'A', 32, 'BSIT');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `conflicts`
--
ALTER TABLE `conflicts`
  ADD PRIMARY KEY (`conflict_id`);

--
-- Indexes for table `courses`
--
ALTER TABLE `courses`
  ADD PRIMARY KEY (`course_id`),
  ADD UNIQUE KEY `course_code` (`course_code`);

--
-- Indexes for table `instructors`
--
ALTER TABLE `instructors`
  ADD PRIMARY KEY (`instructor_id`),
  ADD UNIQUE KEY `username` (`username`);

--
-- Indexes for table `rooms`
--
ALTER TABLE `rooms`
  ADD PRIMARY KEY (`room_id`),
  ADD UNIQUE KEY `room_number` (`room_number`);

--
-- Indexes for table `room_availability`
--
ALTER TABLE `room_availability`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `room_feedback`
--
ALTER TABLE `room_feedback`
  ADD PRIMARY KEY (`feedback_id`);

--
-- Indexes for table `room_programs`
--
ALTER TABLE `room_programs`
  ADD PRIMARY KEY (`room_id`,`program_name`);

--
-- Indexes for table `schedules`
--
ALTER TABLE `schedules`
  ADD PRIMARY KEY (`schedule_id`);

--
-- Indexes for table `subjects`
--
ALTER TABLE `subjects`
  ADD PRIMARY KEY (`subject_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `conflicts`
--
ALTER TABLE `conflicts`
  MODIFY `conflict_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=54;

--
-- AUTO_INCREMENT for table `courses`
--
ALTER TABLE `courses`
  MODIFY `course_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT for table `instructors`
--
ALTER TABLE `instructors`
  MODIFY `instructor_id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=35;

--
-- AUTO_INCREMENT for table `rooms`
--
ALTER TABLE `rooms`
  MODIFY `room_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=48;

--
-- AUTO_INCREMENT for table `room_availability`
--
ALTER TABLE `room_availability`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `room_feedback`
--
ALTER TABLE `room_feedback`
  MODIFY `feedback_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `schedules`
--
ALTER TABLE `schedules`
  MODIFY `schedule_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=1107;

--
-- AUTO_INCREMENT for table `subjects`
--
ALTER TABLE `subjects`
  MODIFY `subject_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=27;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `room_programs`
--
ALTER TABLE `room_programs`
  ADD CONSTRAINT `room_programs_ibfk_1` FOREIGN KEY (`room_id`) REFERENCES `rooms` (`room_id`) ON DELETE CASCADE;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
