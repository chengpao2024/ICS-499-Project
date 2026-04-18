<?php
declare(strict_types=1);
session_start();

require_once __DIR__ . '/../config/db.php'; // ensure this path is correct

$error = '';
$success = '';

// Fetch available assets for dropdown
$assets = [];
$categories = [];
$result = $conn->query("SELECT asset_id, asset_name, asset_category FROM assets WHERE asset_status = 'available'");
if ($result) {
    while ($row = $result->fetch_assoc()) {
        $assets[] = $row;
        if (!in_array($row['asset_category'], $categories)) {
            $categories[] = $row['asset_category'];
        }
    }
}

// Form defaults
$form = [
    'asset_id' => '',
    'asset_category' => '',
    'user_name' => '',
    'rent_start' => '',
    'rent_end' => '',
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $form['asset_id'] = $_POST['asset_id'] ?? '';
    $form['asset_category'] = $_POST['asset_category'] ?? '';
    $form['user_name'] = trim($_POST['user_name'] ?? '');
    $form['rent_start'] = $_POST['rent_start'] ?? '';
    $form['rent_end'] = $_POST['rent_end'] ?? '';

    // Validation
    if ($form['asset_id'] === '' || $form['asset_category'] === '' || $form['user_name'] === '' || $form['rent_start'] === '' || $form['rent_end'] === '') {
        $error = 'All fields are required.';
    } elseif (strtotime($form['rent_start']) > strtotime($form['rent_end'])) {
        $error = 'Start date cannot be after end date.';
    } else {
        // Insert into rental_requests table
        $stmt = $conn->prepare("INSERT INTO rental_requests (asset_id, student_id, faculty_id, requested_start, requested_due, request_status) VALUES (?, NULL, NULL, ?, ?, 'Pending')");
        if (!$stmt) {
            $error = 'Database prepare failed: ' . $conn->error;
        } else {
            $stmt->bind_param(
                'iss',
                $form['asset_id'],
                $form['rent_start'],
                $form['rent_end']
            );
            if ($stmt->execute()) {
                $success = 'Rental request submitted successfully. Redirecting to dashboard...';
            } else {
                $error = 'Database error: ' . $stmt->error;
            }
            $stmt->close();
        }
    }
}
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CAT - Request Rental</title>
<style>
body { font-family: Arial, sans-serif; background:#f6f7fb; margin:0; }
header { background:#fff; padding:16px 24px; border-bottom:1px solid #eee; }
.container { max-width:600px; margin:24px auto; padding:0 16px; }
.card { background:#fff; border:1px solid #eee; border-radius:14px; padding:18px; }
label { font-size: 13px; color:#333; display:block; margin-top:12px; }
input, select { width:90%; padding:12px; margin-top:6px; border:1px solid #ddd; border-radius:10px; }
button { margin-top:14px; padding:12px 14px; border:0; border-radius:10px; background:#1f5cff; color:#fff; font-weight:700; cursor:pointer; }
.msg { padding:10px; border-radius:10px; margin-bottom:14px; }
.err { background:#ffe8e8; border:1px solid #ffb3b3; color:#8a1f1f; }
.ok { background:#e8fff0; border:1px solid #b3ffd0; color:#1f6b3a; }
</style>
</head>
<body>
<header>
  <b>Campus Asset Tracker</b> — Request Rental
</header>

<div class="container">
  <div class="card">
    <?php if ($error): ?><div class="msg err"><?= htmlspecialchars($error) ?></div><?php endif; ?>
    
    //Redirects to dashboard after successful rental request.
    <?php if ($success): ?>
        <div class="msg ok"><?= htmlspecialchars($success) ?></div>

        <script>
            setTimeout(function() {
                window.location.href = "../dashboard/dashboard.py";
            }, 2000); // 2 seconds
        </script>
    <?php endif; ?>

    <form method="post" novalidate>
        <label>Asset Name *</label>
        <select name="asset_id" required>
            <option value="">-- Select Asset --</option>
            <?php foreach ($assets as $a): ?>
                <option value="<?= $a['asset_id'] ?>" <?= $form['asset_id'] == $a['asset_id'] ? 'selected' : '' ?>>
                    <?= htmlspecialchars($a['asset_name']) ?>
                </option>
            <?php endforeach; ?>
        </select>

        <label>Asset Category *</label>
        <select name="asset_category" required>
            <option value="">-- Select Category --</option>
            <?php foreach ($categories as $c): ?>
                <option value="<?= htmlspecialchars($c) ?>" <?= $form['asset_category'] == $c ? 'selected' : '' ?>>
                    <?= htmlspecialchars($c) ?>
                </option>
            <?php endforeach; ?>
        </select>

        <label>Student/Faculty Name *</label>
        <input type="text" name="user_name" value="<?= htmlspecialchars($form['user_name']) ?>" required>

        <label>Rental Start Date *</label>
        <input type="date" name="rent_start" value="<?= htmlspecialchars($form['rent_start']) ?>" required>

        <label>Rental End Date *</label>
        <input type="date" name="rent_end" value="<?= htmlspecialchars($form['rent_end']) ?>" required>

        <button type="submit">Request Rental</button>
    </form>
  </div>
</div>
</body>
</html>