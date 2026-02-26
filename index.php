<?php
session_start();

$error = "";

if ($_SERVER["REQUEST_METHOD"] == "POST") {

    $username = $_POST['username'];
    $password = $_POST['password'];

    // Hardcoded users
    $users = [
        "admin" => ["password" => "admin", "role" => "admin"],
        "faculty" => ["password" => "faculty", "role" => "faculty"],
        "student" => ["password" => "student", "role" => "student"]
    ];

    if (isset($users[$username]) && $users[$username]['password'] === $password) {

        $_SESSION['user'] = $username;
        $_SESSION['role'] = $users[$username]['role'];

        // Redirect based on role
        if ($_SESSION['role'] === "admin") {
            header("Location: dashboard.php");
        } else {
            header("Location: home.php");
        }
        exit();

    } else {
        $error = "Invalid username or password!";
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>CAT Login</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>

<div class="login-container">
    <h2>Campus Asset Tracker (CAT)</h2>
    <h3>Login</h3>

    <?php if ($error != "") { ?>
        <p class="error"><?php echo $error; ?></p>
    <?php } ?>

    <form method="POST" action="">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>

</div>

</body>
</html>