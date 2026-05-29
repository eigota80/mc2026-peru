<?php
	require("../library/Exception.php");
	require("../library/PHPMailer.php");
	require("../library/SMTP.php");

	use PHPMailer\PHPMailer\PHPMailer;
	use PHPMailer\PHPMailer\Exception;

	date_default_timezone_set('America/Bogota');
	setlocale(LC_ALL,"es_ES");
	$motivo;$departamento;$ciudad;$razonsocial;$noDocumento;$nombre;$direccion;$telefono;$extension;$celular;$email;$comentarios;$politicas;$captcha;
	if(isset($_POST['motivo'])){
		$motivo=$_POST['motivo'];
	}
	if(isset($_POST['departamento'])){
		$departamento=$_POST['departamento'];
	}
	if(isset($_POST['ciudad'])){
		$ciudad=$_POST['ciudad'];
	}
	if(isset($_POST['razonsocial'])){
		$razonsocial=$_POST['razonsocial'];
	}
	if(isset($_POST['noDocumento'])){
		$noDocumento=$_POST['noDocumento'];
	}
	if(isset($_POST['nombre'])){
		$nombre=$_POST['nombre'];
	}
	if(isset($_POST['direccion'])){
		$direccion=$_POST['direccion'];
	}
	if(isset($_POST['telefono'])){
		$telefono=$_POST['telefono'];
	}
	if(isset($_POST['extension'])){
		$extension=$_POST['extension'];
	}
	if(isset($_POST['celular'])){
		$celular=$_POST['celular'];
	}
	if(isset($_POST['email'])){
		$email=$_POST['email'];
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
		$haveAttachOk = true;
		$haveAttachDetect = 1;
		$attachOk = true;
		//Get the uploaded file information
		$name_of_uploaded_file = basename($_FILES['fileUpload']['name']);
		//get the file extension of the file
		$type_of_uploaded_file = substr($name_of_uploaded_file, strrpos($name_of_uploaded_file, '.') + 1);
		$size_of_uploaded_file = $_FILES["fileUpload"]["size"]/1024; //size in KBs
		//copy the temp. uploaded file to uploads folder
		$upload_folder = "../upload/";
		$path_of_uploaded_file = $upload_folder . $name_of_uploaded_file;
		$tmp_path = $_FILES["fileUpload"]["tmp_name"];

		if(is_uploaded_file($tmp_path)){
			if(!copy($tmp_path,$path_of_uploaded_file)){
				$attachOk = false;
			}
		}

		//Settings
		$max_allowed_file_size = 17000; // size in KB
		$allowed_extensions = array("jpg", "jpeg", "gif", "png", "xlsx", "doc", "docx", "pdf");

		//Validations
		if($size_of_uploaded_file > $max_allowed_file_size ){
			$attachOk = false;
		}
		if($size_of_uploaded_file < $haveAttachDetect ){
			$haveAttachOk = false;
		}

		//------ Validate the file extension -----
		$allowed_ext = false;
		for($i=0; $i<sizeof($allowed_extensions); $i++){
			if(strcasecmp($allowed_extensions[$i],$type_of_uploaded_file) == 0){
				$allowed_ext = true;
			}
		}

		if(!$allowed_ext){
			$attachOk = false;
		}

		$randImg = rand(0, 6);
		$protocolo = "https://";
		$pathimg= ($protocolo.$_SERVER['HTTP_HOST']."/");
		$web = ($_SERVER['HTTP_HOST']);
		$date = strftime("%d de %B, %Y");

		$motivo = filter_input(INPUT_POST, 'motivo');
		$departamento = filter_input(INPUT_POST, 'departamento');
		$ciudad = filter_input(INPUT_POST, 'ciudad');
		$razonsocial = filter_input(INPUT_POST, 'razonsocial');
		$noDocumento = filter_input(INPUT_POST, 'noDocumento');
		$nombre = filter_input(INPUT_POST, 'nombre');
		$direccion = filter_input(INPUT_POST, 'direccion');
		$telefono = filter_input(INPUT_POST, 'telefono');
		$extension = filter_input(INPUT_POST, 'extension');
		$celular = filter_input(INPUT_POST, 'celular');
		$email = filter_input(INPUT_POST, 'email');
		$comentarios = filter_input(INPUT_POST, 'comentarios');
		$politicas = filter_input(INPUT_POST, 'guardaDatos');

		clearDataSend($motivo);
		clearDataSend($departamento);
		clearDataSend($ciudad);
		clearDataSend($razonsocial);
		clearDataSend($noDocumento);
		clearDataSend($nombre);
		clearDataSend($direccion);
		clearDataSend($telefono);
		clearDataSend($extension);
		clearDataSend($celular);
		clearDataSend($email);
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

		$body = file_get_contents('../templates/pqrs.html');
		$body = str_replace('%identificadorPromo%', $randImg, $body);
		$body = str_replace('%pathimg%', $pathimg, $body);
		$body = str_replace('%web%', $web, $body);
		$body = str_replace('%date%', $date, $body);
		$body = str_replace('%motivo%', $motivo, $body);
		$body = str_replace('%departamento%', $departamento, $body);
		$body = str_replace('%ciudad%', $ciudad, $body);
		$body = str_replace('%razonsocial%', $razonsocial, $body);
		$body = str_replace('%noDocumento%', $noDocumento, $body);
		$body = str_replace('%nombre%', $nombre, $body);
		$body = str_replace('%direccion%', $direccion, $body);
		$body = str_replace('%telefono%', $telefono, $body);
		$body = str_replace('%extension%', $extension, $body);
		$body = str_replace('%celular%', $celular, $body);
		$body = str_replace('%email%', $email, $body);
		$body = str_replace('%politicas%', $politicas, $body);
		$body = str_replace('%comentarios%', $comentarios, $body);
		$body = str_replace('%pathlog%', $logs, $body);
		$body = str_replace('%securityInformation%', $security, $body);

$smtpUsername = getenv('MC_SMTP_USERNAME') ?: 'servicioalcliente@mediacommerce.ec';
$smtpPassword = getenv('MC_SMTP_PASSWORD') ?: '';
$fromAddress = getenv('MC_SMTP_FROM') ?: $smtpUsername;
$recipientAddress = getenv('MC_PQRS_RECIPIENT') ?: 'servicioalcliente@mediacommerce.ec';
$ccAddress = getenv('MC_PQRS_CC') ?: '';

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
		$mail->Subject = $nombre." tiene una nueva PQRS! 😬";
		$mail->MsgHTML($body);

		$mail->Body = $body;
		if($attachOk == true){
			$mail->addAttachment($path_of_uploaded_file);
		}else{
			if($haveAttachOk == true ){
				header('Location:'.$_SERVER['HTTP_REFERER']."?file");
				exit();
			}
		}
		$exito = $mail->Send();
		if($exito){

			$log=date("Y-m-d H:i:s") . ";" . $_SERVER['REMOTE_ADDR'] . ";" . $motivo.";" .$departamento.";" .$ciudad.";" .$razonsocial.";" .$noDocumento.";" .$nombre.";" .$direccion.";" .$telefono.";" .$extension.";" .$celular.";" .$email.";" .$politicas. ";" .$comentarios;

			$file = fopen("../../logs/account/data/pqrs/pqrs.csv", "a+");
				fwrite($file, $log . PHP_EOL);
				fclose($file);

			$nombre = str_replace(' ', '%', $nombre);
			$nombre = str_replace('ñ', 'n', $nombre);

			unlink($path_of_uploaded_file);

			header('Location: /gracias.html?name='. $nombre.'&type=1');

		}else{
			$log=date("Y-m-d H:i:s") . ";" . $_SERVER['REMOTE_ADDR'] . ";" . $mail->ErrorInfo . ";" . "Error de formulario. Contáctenos!";

			$file = fopen("../../logs/account/data/pqrs/pqrs.csv", "a+");
				fwrite($file, $log . PHP_EOL);
			fclose($file);

			header('Location:'.$_SERVER['HTTP_REFERER']."?wtf");

		}
		exit();
	}
?>
