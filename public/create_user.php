<?php
session_start();
require_once(__DIR__ . "/../config/db.php");

$conn = cat_db();

if ($_SERVER["REQUEST_METHOD"] === "POST") {

    $type = $_POST['user_type'];
    $email = $conn->real_escape_string($_POST['email']);
    $password = password_hash($_POST['password'], PASSWORD_DEFAULT);
    $fname = $conn->real_escape_string($_POST['fname']);
    $lname = $conn->real_escape_string($_POST['lname']);

    if ($type === "student") {
        $cell = $conn->real_escape_string($_POST['cell']);
        $sql = "INSERT INTO students (student_email, student_password, student_cell, student_fname, student_lname)
                VALUES ('$email', '$password', '$cell', '$fname', '$lname')";

    } elseif ($type === "faculty") {
        $department = $conn->real_escape_string($_POST['department']);

        $sql = "INSERT INTO faculty (faculty_email, faculty_password, faculty_fname, faculty_lname, department)
                VALUES ('$email', '$password', '$fname', '$lname', '$department')";
    }

    if ($conn->query($sql)) {
        header("Location: manage_users.php");
        exit();
    } else {
        $error = "Error creating user: " . $conn->error;
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>Create User</title>
    <link rel="stylesheet" href="admin.css">
    <script>
        function toggleFields() {
            let type = document.getElementById("user_type").value;
            document.getElementById("student_fields").style.display = (type === "student") ? "block" : "none";
            document.getElementById("faculty_fields").style.display = (type === "faculty") ? "block" : "none";
        }
    </script>
</head>
<body onload="toggleFields()">

<h1>Create User</h1>

<?php if (isset($error)) { ?>
    <p style="color:red;"><?= $error; ?></p>
<?php } ?>

<form method="POST">

    <label>User Type:</label><br>
    <select name="user_type" id="user_type" onchange="toggleFields()" required>
        <option value="student">Student</option>
        <option value="faculty">Faculty</option>
    </select>
    <br><br>

    <label>Email:</label><br>
    <input type="email" name="email" required>
    <br><br>

    <label>Password:</label><br>
    <input type="password" name="password" required>
    <br><br>

    <label>First Name:</label><br>
    <input type="text" name="fname" required>
    <br><br>

    <label>Last Name:</label><br>
    <input type="text" name="lname" required>
    <br><br>

    <!-- Student Only -->
    <div id="student_fields">
        <label>Cell:</label><br>
        <input type="text" name="cell">
        <br><br>
    </div>

    <!-- Faculty Only -->
    <div id="faculty_fields">
        <label>Department:</label><br>
        <input type="text" name="department">
        <br><br>
    </div>

    <button type="submit">Create User</button>
    <a href="manage_users.php" style="margin-left:10px;">Cancel</a>

</form>

</body>
</html>