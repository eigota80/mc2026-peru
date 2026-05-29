<?php
	require("../library/Exception.php");
	require("../library/PHPMailer.php");
	require("../library/SMTP.php");

	use PHPMailer\PHPMailer\PHPMailer;
	use PHPMailer\PHPMailer\Exception;

	date_default_timezone_set('America/Bogota');
	setlocale(LC_ALL,"es_ES");
	$nombre;$email;$empresa;$ciudad;$telefono;$negocio;$comentarios;$politicas;$captcha;

	if(isset($_POST['nombre'])){
		$nombre=$_POST['nombre'];
	}
	if(isset($_POST['email'])){
		$email=$_POST['email'];
	}
	if(isset($_POST['empresa'])){
		$empresa=$_POST['empresa'];
	}
	if(isset($_POST['ciudad'])){
		$ciudad=$_POST['ciudad'];
	}
	if(isset($_POST['telefono'])){
		$telefono=$_POST['telefono'];
	}
	if(isset($_POST['negocio'])){
		$negocio=$_POST['negocio'];
	}
	if(isset($_POST['comentarios'])){
		$comentarios=$_POST['comentarios'];
	}
	if(isset($_POST['guardaDatos'])){
		$politicas=$_POST['guardaDatos'];
	}
	if(isset($_POST['g-recaptcha-response'])){
		$captcha=$_POST['g-recaptcha-response'];
	}
	if(!$captcha){
		header('Location:'.$_SERVER['HTTP_REFERER'].'?captcha');
		exit();
	}
	require("../library/secretKey.php");
	if(!validateRecaptcha($secretKey, $captcha))
	{
		header('Location:'.$_SERVER['HTTP_REFERER']."?captcha");
		exit();
	}else{
		$redirectionSegment = array(
			array("Connection","segmento/connection.csv"),
			array("Cloud","segmento/cloud.csv"),
			array("Collaboration","segmento/collaboration.csv"),
			array("Security","segmento/security.csv"),
			array("Otro servicio","contacto.csv"),
		);
		$randImg = rand(0, 6);
		$protocolo = "https://";
		$pathimg= ($protocolo.$_SERVER['HTTP_HOST']."/");
		$web = ($_SERVER['HTTP_HOST']);
		$date = strftime("%d de %B, %Y");
		$nombre = filter_input(INPUT_POST, 'nombre');
		$email = filter_input(INPUT_POST, 'email');
		$empresa = filter_input(INPUT_POST, 'empresa');
		$ciudad = filter_input(INPUT_POST, 'ciudad');
		$telefono = filter_input(INPUT_POST, 'telefono');
		$negocio = filter_input(INPUT_POST, 'negocio');
		$comentarios = filter_input(INPUT_POST, 'comentarios');
		$politicas = filter_input(INPUT_POST, 'guardaDatos');

		clearDataSend($nombre);
		clearDataSend($email);
		clearDataSend($empresa);
		clearDataSend($ciudad);
		clearDataSend($telefono);
		clearDataSend($negocio);
		clearDataSend($comentarios);
		clearDataSend($politicas);

		$logs = ($protocolo.$_SERVER['HTTP_HOST']."/logs");
		$security =
			$_SERVER['PHP_SELF']."<br>".
			$_SERVER['SERVER_NAME']."<br>".
			$_SERVER['HTTP_HOST']."<br>".
			$_SERVER['HTTP_REFERER']."<br>".
			$_SERVER['HTTP_USER_AGENT']."<br>".
			$_SERVER['REQUEST_METHOD']."<br>".
			$_SERVER['REQUEST_TIME']."<br>".
			$_SERVER['REMOTE_ADDR']."<br>";

		$body = file_get_contents('../templates/main.html');
		$body = str_replace('%identificadorPromo%', $randImg, $body);
		$body = str_replace('%pathimg%', $pathimg, $body);
		$body = str_replace('%web%', $web, $body);
		$body = str_replace('%date%', $date, $body);
		$body = str_replace('%nombre%', $nombre, $body);
		$body = str_replace('%email%', $email, $body);
		$body = str_replace('%empresa%', $empresa, $body);
		$body = str_replace('%ciudad%', $ciudad, $body);
		$body = str_replace('%telefono%', $telefono, $body);
		$body = str_replace('%negocio%', $redirectionSegment[$negocio][0], $body);
		$body = str_replace('%politicas%', $politicas, $body);
		$body = str_replace('%comentarios%', $comentarios, $body);
		$body = str_replace('%pathlog%', $logs, $body);
		$body = str_replace('%securityInformation%', $security, $body);

$smtpUsername = getenv('MC_SMTP_USERNAME') ?: 'servicioalcliente@mediacommerce.ec';
$smtpPassword = getenv('MC_SMTP_PASSWORD') ?: '';
$fromAddress = getenv('MC_SMTP_FROM') ?: $smtpUsername;
$recipientAddress = getenv('MC_CONTACT_RECIPIENT') ?: 'servicioalcliente@mediacommerce.ec';
$ccAddress = getenv('MC_CONTACT_CC') ?: 'marketing@mediacommerce.ec';

		$mail = new PHPMailer();

		$mail->IsSMTP();
		$mail->Host = "smtp.gmail.com";
		$mail->SMTPAuth = true;
		$mail->SMTPSecure = 'ssl';
		$mail->Port = 465;
		$mail->Username = $smtpUsername;
		$mail->Password = $smtpPassword;

		$mail->AddAddress($recipientAddress);
		if(!empty($ccAddress)){
			$mail->AddCC($ccAddress);
		}

		$mail->AddReplyTo($email, $nombre);
		$mail->SetFrom($fromAddress, 'Media Commerce Ecuador');
		$mail->ReturnPath = $fromAddress;

		$mail->IsHTML(true);
		$mail->CharSet = 'UTF-8';
		$mail->Subject = $nombre." te ha enviado un mensaje. ¡Está interesado en ".$redirectionSegment[$negocio][0]."! 🎉";
		$mail->MsgHTML($body);

		$mail->Body = $body;
		$exito = $mail->Send();
		if($exito){
			$log=date("Y-m-d H:i:s") . ";" . $_SERVER['REMOTE_ADDR'] . ";" . $nombre.";" .$email. ";" .$telefono. ";" .$ciudad. ";" .$empresa. ";" .$politicas. ";" .$comentarios;

			$file = fopen("../../logs/account/data/".$redirectionSegment[$negocio][1], "a+");
				fwrite($file, $log . PHP_EOL);
				fclose($file);

			$nombre = str_replace(' ', '%', $nombre);
			$nombre = str_replace('ñ', 'n', $nombre);
			header('Location: /gracias.html?name='. $nombre);

		}else{
			$log=date("Y-m-d H:i:s") . ";" . $_SERVER['REMOTE_ADDR'] . ";" . $mail->ErrorInfo . ";" . "Error de formulario. Contáctenos!";

			$file = fopen("../../logs/account/data/".$redirectionSegment[$negocio][1], "a+");
				fwrite($file, $log . PHP_EOL);
			fclose($file);

			header('Location:'.$_SERVER['HTTP_REFERER']."?wtf");

		}
		exit();
	}
?>
