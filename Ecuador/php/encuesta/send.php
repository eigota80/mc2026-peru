<?php
	require("../library/Exception.php");
	require("../library/PHPMailer.php");
	require("../library/SMTP.php");

	use PHPMailer\PHPMailer\PHPMailer;
	use PHPMailer\PHPMailer\Exception;

	date_default_timezone_set('America/Bogota');
	setlocale(LC_ALL,"es_ES");
	$nombre;$email;$telefono;$nit;$cargo;$p1;$p1porque;$p2;$p2porque;$slider1;$slider2;$slider3;$p3;$p3porque;$slider4;$slider5;$slider6;$p4;$p4porque;$p5;$p5porque;$slider7;$p6;$p6porque;$politicas;$captcha;

	if(isset($_POST['nombre'])){
		$nombre=$_POST['nombre'];
	}
	if(isset($_POST['email'])){
		$email=$_POST['email'];
	}
	if(isset($_POST['telefono'])){
		$telefono=$_POST['telefono'];
	}
	if(isset($_POST['nit'])){
		$nit=$_POST['nit'];
	}
	if(isset($_POST['cargo'])){
		$cargo=$_POST['cargo'];
	}
	if(isset($_POST['p-1'])){
		$p1=$_POST['p-1'];
	}
	if(isset($_POST['p-1-porque'])){
		$p1porque=$_POST['p-1-porque'];
	}
	if(isset($_POST['p-2'])){
		$p2=$_POST['p-2'];
	}
	if(isset($_POST['p-2-porque'])){
		$p2porque=$_POST['p-2-porque'];
	}
	if(isset($_POST['slider-1'])){
		$slider1=$_POST['slider-1'];
	}
	if(isset($_POST['slider-2'])){
		$slider2=$_POST['slider-2'];
	}
	if(isset($_POST['slider-3'])){
		$slider3=$_POST['slider-3'];
	}
	if(isset($_POST['p-3'])){
		$p3=$_POST['p-3'];
	}
	if(isset($_POST['p-3-porque'])){
		$p3porque=$_POST['p-3-porque'];
	}
	if(isset($_POST['slider-4'])){
		$slider4=$_POST['slider-4'];
	}
	if(isset($_POST['slider-5'])){
		$slider5=$_POST['slider-5'];
	}
	if(isset($_POST['slider-6'])){
		$slider6=$_POST['slider-6'];
	}
	if(isset($_POST['p-4'])){
		$p4=$_POST['p-4'];
	}
	if(isset($_POST['p-4-porque'])){
		$p4porque=$_POST['p-4-porque'];
	}
	if(isset($_POST['p-5'])){
		$p5=$_POST['p-5'];
	}
	if(isset($_POST['p-5-porque'])){
		$p5porque=$_POST['p-5-porque'];
	}
	if(isset($_POST['slider-7'])){
		$slider7=$_POST['slider-7'];
	}
	if(isset($_POST['p-6'])){
		$p6=$_POST['p-6'];
	}
	if(isset($_POST['p-6-porque'])){
		$p6porque=$_POST['p-6-porque'];
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
		$randImg = rand(0, 6);
		$protocolo = "https://";
		$pathimg= ($protocolo.$_SERVER['HTTP_HOST']."/");
		$web = ($_SERVER['HTTP_HOST']);
		$date = strftime("%d de %B, %Y");
		$nombre = filter_input(INPUT_POST, 'nombre');
		$email = filter_input(INPUT_POST, 'email');
		$telefono = filter_input(INPUT_POST, 'telefono');
		$nit = filter_input(INPUT_POST, 'nit');
		$cargo = filter_input(INPUT_POST, 'cargo');
		$p1 = filter_input(INPUT_POST, 'p-1');
		$p1porque = filter_input(INPUT_POST, 'p-1-porque');
		$p2 = filter_input(INPUT_POST, 'p-2');
		$p2porque = filter_input(INPUT_POST, 'p-2-porque');
		$slider1 = filter_input(INPUT_POST, 'slider-1');
		$slider2 = filter_input(INPUT_POST, 'slider-2');
		$slider3 = filter_input(INPUT_POST, 'slider-3');
		$p3 = filter_input(INPUT_POST, 'p-3');
		$p3porque = filter_input(INPUT_POST, 'p-3-porque');
		$slider4 = filter_input(INPUT_POST, 'slider-4');
		$slider5 = filter_input(INPUT_POST, 'slider-5');
		$slider6 = filter_input(INPUT_POST, 'slider-6');
		$p4 = filter_input(INPUT_POST, 'p-4');
		$p4porque = filter_input(INPUT_POST, 'p-4-porque');
		$p5 = filter_input(INPUT_POST, 'p-5');
		$p5porque = filter_input(INPUT_POST, 'p-5-porque');
		$slider7 = filter_input(INPUT_POST, 'slider-7');
		$p6 = filter_input(INPUT_POST, 'p-6');
		$p6porque = filter_input(INPUT_POST, 'p-6-porque');
		$politicas = filter_input(INPUT_POST, 'guardaDatos');

		clearDataSend($nombre);
		clearDataSend($email);
		clearDataSend($telefono);
		clearDataSend($nit);
		clearDataSend($cargo);
		clearDataSend($p1);
		clearDataSend($p1porque);
		clearDataSend($p2);
		clearDataSend($p2porque);
		clearDataSend($slider1);
		clearDataSend($slider2);
		clearDataSend($slider3);
		clearDataSend($p3);
		clearDataSend($p3porque);
		clearDataSend($slider4);
		clearDataSend($slider5);
		clearDataSend($slider6);
		clearDataSend($p4);
		clearDataSend($p4porque);
		clearDataSend($p5);
		clearDataSend($p5porque);
		clearDataSend($slider7);
		clearDataSend($p6);
		clearDataSend($p6porque);
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

		$body = file_get_contents('../templates/encuesta.html');
		$body = str_replace('%identificadorPromo%', $randImg, $body);
		$body = str_replace('%pathimg%', $pathimg, $body);
		$body = str_replace('%web%', $web, $body);
		$body = str_replace('%date%', $date, $body);
		$body = str_replace('%nombre%', $nombre, $body);
		$body = str_replace('%email%', $email, $body);
		$body = str_replace('%telefono%', $telefono, $body);
		$body = str_replace('%nit%', $nit, $body);
		$body = str_replace('%cargo%', $cargo, $body);
		$body = str_replace('%p1%', $p1, $body);
		$body = str_replace('%p1porque%', $p1porque, $body);
		$body = str_replace('%p2%', $p2, $body);
		$body = str_replace('%p2porque%', $p2porque, $body);
		$body = str_replace('%slider1%', $slider1, $body);
		$body = str_replace('%slider2%', $slider2, $body);
		$body = str_replace('%slider3%', $slider3, $body);
		$body = str_replace('%p3%', $p3, $body);
		$body = str_replace('%p3porque%', $p3porque, $body);
		$body = str_replace('%slider4%', $slider4, $body);
		$body = str_replace('%slider5%', $slider5, $body);
		$body = str_replace('%slider6%', $slider6, $body);
		$body = str_replace('%p4%', $p4, $body);
		$body = str_replace('%p4porque%', $p4porque, $body);
		$body = str_replace('%p5%', $p5, $body);
		$body = str_replace('%p5porque%', $p5porque, $body);
		$body = str_replace('%slider7%', $slider7, $body);
		$body = str_replace('%p6%', $p6, $body);
		$body = str_replace('%p6porque%', $p6porque, $body);
		$body = str_replace('%politicas%', $politicas, $body);
		$body = str_replace('%pathlog%', $logs, $body);
		$body = str_replace('%securityInformation%', $security, $body);

$smtpUsername = getenv('MC_SMTP_USERNAME') ?: 'servicioalcliente@mediacommerce.ec';
$smtpPassword = getenv('MC_SMTP_PASSWORD') ?: '';
$fromAddress = getenv('MC_SMTP_FROM') ?: $smtpUsername;
$recipientAddress = getenv('MC_ENCUESTA_RECIPIENT') ?: 'servicioalcliente@mediacommerce.ec';
$ccAddress = getenv('MC_ENCUESTA_CC') ?: '';

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
		$mail->Subject = $nombre." te ha enviado su encuesta de satisfacción! 🤗";
		$mail->MsgHTML($body);

		$mail->Body = $body;
		$exito = $mail->Send();
		if($exito){

			$log=date("Y-m-d H:i:s") . ";" . $_SERVER['REMOTE_ADDR'] . ";" . $nombre.";" .$email. ";" .$telefono. ";" .$nit.";" .$cargo.";" .$p1.".&#032" .$p1porque.";" .$p2.".&#032" .$p2porque.";" .$slider1.";" .$slider2.";" .$slider3.";" .$p3.".&#032" .$p3porque.";" .$slider4.";" .$slider5.";" .$slider6.";" .$p4.".&#032" .$p4porque.";" .$p5.".&#032" .$p5porque.";" .$slider7.";" .$p6.".&#032" .$p6porque.";" .$politicas.";" ;

			$file = fopen("../../logs/account/data/encuesta/encuesta-de-satisfaccion.csv", "a+");
				fwrite($file, $log . PHP_EOL);
				fclose($file);

			$nombre = str_replace(' ', '%', $nombre);
			$nombre = str_replace('ñ', 'n', $nombre);
			header('Location: /gracias.html?name='. $nombre.'&type=0');

		}else{
			$log=date("Y-m-d H:i:s") . ";" . $_SERVER['REMOTE_ADDR'] . ";" . $mail->ErrorInfo . ";" . "Error de formulario. Contáctenos!";

			$file = fopen("../../logs/account/data/encuesta/encuesta-de-satisfaccion.csv", "a+");
				fwrite($file, $log . PHP_EOL);
			fclose($file);

			header('Location:'.$_SERVER['HTTP_REFERER']."?wtf");

		}
		exit();
	}
?>
