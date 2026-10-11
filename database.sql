-- ============================================================
-- LOCUS - Library Hot Desking System
-- Database: library_hotdesking
-- ============================================================

CREATE DATABASE IF NOT EXISTS library_hotdesking
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE library_hotdesking;

-- ============================================================
-- TABLE: users
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    user_id     INT          NOT NULL AUTO_INCREMENT,
    name        VARCHAR(150) NOT NULL,
    email       VARCHAR(255) NOT NULL,
    student_id  VARCHAR(50)  NOT NULL,
    password    VARCHAR(255) NOT NULL,  -- bcrypt hash
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (user_id),
    UNIQUE KEY uq_users_email      (email),
    UNIQUE KEY uq_users_student_id (student_id)
) ENGINE=InnoDB;


-- ============================================================
-- TABLE: seats
-- ============================================================
CREATE TABLE IF NOT EXISTS seats (
    seat_id     INT         NOT NULL AUTO_INCREMENT,
    seat_number VARCHAR(20) NOT NULL,
    floor       INT         NOT NULL,
    status      ENUM('available', 'maintenance') NOT NULL DEFAULT 'available',

    PRIMARY KEY (seat_id),
    UNIQUE KEY uq_seats_seat_number (seat_number)
) ENGINE=InnoDB;


-- ============================================================
-- TABLE: bookings
-- ============================================================
CREATE TABLE IF NOT EXISTS bookings (
    booking_id   INT  NOT NULL AUTO_INCREMENT,
    user_id      INT  NOT NULL,
    seat_id      INT  NOT NULL,
    booking_date DATE NOT NULL,
    start_time   TIME NOT NULL,
    end_time     TIME NOT NULL,
    status       ENUM('confirmed', 'cancelled', 'completed', 'expired', 'no_show')
                 NOT NULL DEFAULT 'confirmed',
    created_at   TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (booking_id),

    CONSTRAINT fk_bookings_user
        FOREIGN KEY (user_id)  REFERENCES users (user_id)  ON DELETE CASCADE,

    CONSTRAINT fk_bookings_seat
        FOREIGN KEY (seat_id)  REFERENCES seats (seat_id)  ON DELETE RESTRICT,

    -- Indexes to speed up overlap queries and user-booking lookups
    INDEX idx_bookings_seat_date   (seat_id, booking_date),
    INDEX idx_bookings_user        (user_id),
    INDEX idx_bookings_status      (status),
    INDEX idx_bookings_date_times  (booking_date, start_time, end_time)
) ENGINE=InnoDB;


-- ============================================================
-- TABLE: attendance
-- ============================================================
CREATE TABLE IF NOT EXISTS attendance (
    attendance_id   INT      NOT NULL AUTO_INCREMENT,
    booking_id      INT      NOT NULL,
    check_in_time   DATETIME NULL     DEFAULT NULL,
    check_out_time  DATETIME NULL     DEFAULT NULL,
    status          ENUM('present', 'no_show') NOT NULL DEFAULT 'no_show',

    PRIMARY KEY (attendance_id),
    UNIQUE KEY uq_attendance_booking (booking_id),   -- one record per booking

    CONSTRAINT fk_attendance_booking
        FOREIGN KEY (booking_id) REFERENCES bookings (booking_id) ON DELETE CASCADE
) ENGINE=InnoDB;


-- ============================================================
-- SAMPLE SEATS
-- Floor 1: A-wing (A01–A08)
-- Floor 2: B-wing (B01–B04)
-- ============================================================
INSERT INTO seats (seat_number, floor, status) VALUES
    ('A01', 1, 'available'),
    ('A02', 1, 'available'),
    ('A03', 1, 'available'),
    ('A04', 1, 'available'),
    ('A05', 1, 'available'),
    ('A06', 1, 'available'),
    ('A07', 1, 'available'),
    ('A08', 1, 'available'),
    ('B01', 2, 'available'),
    ('B02', 2, 'available'),
    ('B03', 2, 'available'),
    ('B04', 2, 'available')
ON DUPLICATE KEY UPDATE seat_number = seat_number;  -- idempotent re-run
