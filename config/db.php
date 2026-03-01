<?php
declare(strict_types=1);

$host = 'localhost';
$user = 'root';
$pass = '';
$db   = 'cat_db';

$conn = new mysqli($host, $user, $pass, $db);

if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}

function cat_db(): mysqli {
    global $conn;
    return $conn;
}