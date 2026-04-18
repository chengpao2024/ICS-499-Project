<?php
session_start();
require_once("config/db.php");

// check if admin is logged in
if (!isset($_SESSION['admin_id'])) {
    header("Location: index.php");
    exit();
}

$conn = cat_db();

// delete student
if (isset($_GET['delete_student'])) {
    $id = $_GET['delete_student'];
    $sql = "DELETE FROM students WHERE student_id = $id";
    $conn->query($sql);

    header("Location: manage_users.php");
    exit();
}

// delete faculty
if (isset($_GET['delete_faculty'])) {
    $id = $_GET['delete_faculty'];
    $sql = "DELETE FROM faculty WHERE faculty_id = $id";
    $conn->query($sql);

    header("Location: manage_users.php");
    exit();
}

// get data
$students = $conn->query("SELECT * FROM students");
$faculty = $conn->query("SELECT * FROM faculty");
?>

<!DOCTYPE html>
<html>
<head>
    <title>Manage Users</title>
    <link rel="stylesheet" href="admin.css">
</head>
<body>

<h1>Manage Users</h1>

<h2>Students</h2>
<table class="user-table">
    <tr>
        <th>ID</th>
        <th>Email</th>
        <th>Name</th>
        <th>Cell</th>
        <th>Action</th>
    </tr>

    <?php while ($row = $students->fetch_assoc()) { ?>
    <tr>
        <td><?= $row['student_id']; ?></td>
        <td><?= $row['student_email']; ?></td>
        <td><?= $row['student_fname'] . " " . $row['student_lname']; ?></td>
        <td><?= $row['student_cell']; ?></td>
        <td>
            <a class="delete-btn"
               href="manage_users.php?delete_student=<?= $row['student_id']; ?>"
               onclick="return confirm('Delete this student?');">
               Delete
            </a>
        </td>
    </tr>
    <?php } ?>
</table>


<h2>Faculty</h2>
<table class="user-table">
    <tr>
        <th>ID</th>
        <th>Email</th>
        <th>Name</th>
        <th>Department</th>
        <th>Action</th>
    </tr>

    <?php while ($row = $faculty->fetch_assoc()) { ?>
    <tr>
        <td><?= $row['faculty_id']; ?></td>
        <td><?= $row['faculty_email']; ?></td>
        <td><?= $row['faculty_fname'] . " " . $row['faculty_lname']; ?></td>
        <td><?= $row['department']; ?></td>
        <td>
            <a class="delete-btn"
               href="manage_users.php?delete_faculty=<?= $row['faculty_id']; ?>"
               onclick="return confirm('Delete this faculty member?');">
               Delete
            </a>
        </td>
    </tr>
    <?php } ?>
</table>

</body>
</html>