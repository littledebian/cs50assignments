-- Keep a log of any SQL queries you execute as you solve the mystery.


-- starting knowledge: july 28, 2021 on humphrey st

-- leads: crime reports
    -- crime occurred 10:15am
-- interviews 3 witness transcripts
    -- atm leggett st
    -- lic plate bakery
    -- phoned accompl to buy flight tix

-- /* MOST RECENT QUERIES ON TOP */ --

-- Number of lic plates at bakery between 10:15 and 10:25
-- +----------+
-- | count(*) |
-- +----------+
-- | 8        |
-- +----------+
-- SELECT  count(*)
-- FROM    bakery_security_logs
-- WHERE   month = 7
-- AND     day = 28
-- AND     hour = 10
-- AND     minute BETWEEN 15 AND 25;

-- Example select joining atm, bakery, phone calls, and passengers
-- +-------+
-- | name  |
-- +-------+
-- | Bruce |
-- +-------+
-- SELECT DISTINCT
--         name
-- FROM    people p
--         JOIN bank_accounts b
--         ON  b.person_id = p.id
--         AND b.account_number IN
--                 (SELECT account_number
--                 FROM   atm_transactions t
--                 WHERE  month = 7
--                 AND    day = 28
--                 AND    t.atm_location = 'Leggett Street')

--         INNER JOIN bakery_security_logs l
--         ON  p.license_plate = l.license_plate
--         AND l.license_plate IN
--                 (SELECT license_plate
--                 FROM   bakery_security_logs l
--                 WHERE  l.month = 7
--                 AND    l.day = 28
--                 AND    hour = 10
--                 AND    minute BETWEEN 15 AND 25)

--         INNER JOIN phone_calls c
--         ON  p.phone_number = c.caller
--         AND c.month = 7
--         AND c.day = 28
--         AND c.duration < 60

--         INNER JOIN passengers s
--         ON  p.passport_number = s.passport_number
--         AND s.flight_id IN
--                 (SELECT id
--                 FROM    flights
--                 WHERE   month = 7
--                 AND     day = 29
--                 AND     hour BETWEEN 0 AND 12);

-- Name of accomplice
-- +-------+
-- | name  |
-- +-------+
-- | Robin |
-- +-------+
-- select name from people p
-- where p.phone_number = '(375) 555-8161';


-- Phone number of the accomplice
-- +-----+----------------+----------------+------+-------+-----+----------+
-- | id  |     caller     |    receiver    | year | month | day | duration |
-- +-----+----------------+----------------+------+-------+-----+----------+
-- | 233 | (367) 555-5533 | (375) 555-8161 | 2021 | 7     | 28  | 45       |
-- +-----+----------------+----------------+------+-------+-----+----------+
-- select *
-- from    phone_calls p
-- where   duration < 61
-- and     p.month = 7
-- and     p.day = 28
-- and     p.caller in
--             (select phone_number from people
--             where name='Bruce');


-- Bruce left bakery at 10:18, consistent with crime scene report
-- +-----+------+-------+-----+------+--------+----------+---------------+
-- | id  | year | month | day | hour | minute | activity | license_plate |
-- +-----+------+-------+-----+------+--------+----------+---------------+
-- | 232 | 2021 | 7     | 28  | 8    | 23     | entrance | 94KL13X       |
-- | 261 | 2021 | 7     | 28  | 10   | 18     | exit     | 94KL13X       |
-- +-----+------+-------+-----+------+--------+----------+---------------+
-- SELECT * FROM bakery_security_logs
-- WHERE license_plate IN
--         (SELECT license_plate FROM people WHERE name='Bruce');


-- Taylor didn't leave bakery until 10:35, therefore Bruce is prime suspect
-- +-----+------+-------+-----+------+--------+----------+---------------+
-- | id  | year | month | day | hour | minute | activity | license_plate |
-- +-----+------+-------+-----+------+--------+----------+---------------+
-- | 237 | 2021 | 7     | 28  | 8    | 34     | entrance | 1106N58       |
-- | 268 | 2021 | 7     | 28  | 10   | 35     | exit     | 1106N58       |
-- +-----+------+-------+-----+------+--------+----------+---------------+
-- SELECT * FROM bakery_security_logs
-- WHERE license_plate IN
--         (SELECT license_plate FROM people WHERE name='Taylor');


-- Both Taylor and Bruce made a w/d on 7/28
-- +------------------+
-- | transaction_type |
-- +------------------+
-- | withdraw         |
-- | withdraw         |
-- +------------------+
-- select  transaction_type
-- from    atm_transactions t,
--         bank_accounts b
-- where   t.atm_location = 'Leggett Street'
-- and     year = 2021
-- and     month = 7
-- and     day = 28
-- and     t.account_number = b.account_number
-- and     b.person_id in
--                 (select id
--                 from    people
--                 where   name='Taylor'
--                 or      name='Bruce');


-- These people at the atm, bakery, made a phone call of under a minute
-- and boarded flight 36
-- +--------+
-- |  name  |
-- +--------+
-- | Bruce  |
-- | Taylor |
-- +--------+
-- select name
-- from
--        people p,
--        atm_transactions t,
--        bank_accounts b,
--        phone_calls c,
--        passengers s
-- where  t.atm_location = 'Leggett Street'
-- and    t.account_number = b.account_number
-- and    b.person_id = p.id
-- and    t.year = 2021
-- and    t.month = 7
-- and    t.day = 28
-- and    p.phone_number = c.caller
-- and    c.duration < 61
-- and    c.year = 2021
-- and    c.month = 7
-- and    c.day = 28
-- and    p.passport_number = s.passport_number
-- and    s.flight_id = 36
-- and    p.license_plate in
--                 (select license_plate
--                 from    bakery_security_logs l
--                 where   l.year = 2021
--                 and     l.month = 7
--                 and     l.day = 28);


-- Destination of flight 36, suspect escaped to NYC
-- +---------------+
-- |     city      |
-- +---------------+
-- | New York City |
-- +---------------+
-- select city from airports where id=4;


-- Earliest flight on 7/29
-- +----+-------------------+------------------------+------+-------+-----+------+--------+
-- | id | origin_airport_id | destination_airport_id | year | month | day | hour | minute |
-- +----+-------------------+------------------------+------+-------+-----+------+--------+
-- | 36 | 8                 | 4                      | 2021 | 7     | 29  | 8    | 20     |
-- +----+-------------------+------------------------+------+-------+-----+------+--------+
-- select * from flights
-- where   year = 2021
-- and     month = 7
-- and     day = 29
-- order by hour asc limit 1;


-- These people visited the Leggett St atm and the bakery on 7/28
-- +--------+----------------+-----------------+---------------+
-- |  name  |  phone_number  | passport_number | license_plate |
-- +--------+----------------+-----------------+---------------+
-- | Luca   | (389) 555-5198 | 8496433585      | 4328GD8       |
-- | Taylor | (286) 555-6063 | 1988161715      | 1106N58       |
-- | Bruce  | (367) 555-5533 | 5773159633      | 94KL13X       |
-- | Iman   | (829) 555-5269 | 7049073643      | L93JTIZ       |
-- | Diana  | (770) 555-1861 | 3592750733      | 322W7JE       |
-- +--------+----------------+-----------------+---------------+
-- SELECT DISTINCT name, phone_number, passport_number, p.license_plate
-- FROM
--       people p,
--       atm_transactions a,
--       bank_accounts b,
--       bakery_security_logs l
-- WHERE a.account_number = b.account_number
-- AND   a.atm_location = 'Leggett Street'
-- AND   b.person_id = p.id
-- AND   l.license_plate = p.license_plate
-- AND   a.year = l.year
-- AND   l.year = 2021
-- AND   a.month = l.month
-- AND   l.month = 7
-- AND   a.day = l.day
-- AND   l.day = 28;


-- According to witnesses:
-- Suspect's plate seen at the bakery after being spotted at the atm
-- then made an outgoing call that lasted under a minute. Suspect claimed
-- to be taking earliest flight the following day

-- SELECT transcript FROM interviews
-- WHERE year = 2021
-- AND   month = 7
-- AND   day = 28;

-- SELECT * FROM crime_scene_reports
-- WHERE year = 2021
-- AND  month = 7
-- AND  day = 28
-- AND  street like 'humphrey%';
