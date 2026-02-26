<?php
session_start();

// Only allow admin
if (!isset($_SESSION['user']) || $_SESSION['role'] !== "admin") {
    header("Location: login.php");
    exit();
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Admin Dashboard</title>
</head>
<body>

<h1>Admin Dashboard</h1>
<h2>Coming Soon.</h2>

<br>
<a href="logout.php">Logout</a>

</body>
</html>