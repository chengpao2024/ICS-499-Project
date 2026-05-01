<?php
session_start();
session_destroy();

// Clear the Python-side auth cookie too
setcookie('cat_session_token', '', [
    'expires'  => time() - 3600,
    'path'     => '/',
    'httponly' => true,
    'samesite' => 'Lax',
]);

header("Location: index.php");
exit();
?>