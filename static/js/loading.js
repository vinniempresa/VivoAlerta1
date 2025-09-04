document.addEventListener('DOMContentLoaded', function() {
    // Selecionar todos os links com classe 'load-transition'
    const transitionLinks = document.querySelectorAll('a.load-transition');
    
    // Adicionar evento de clique a cada link
    transitionLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault(); // Prevenir navegação padrão
            
            // Obter atributos do link
            const href = this.getAttribute('href');
            const tipoTransicao = this.getAttribute('data-tipo') || 'default';
            
            // Criar a URL da página de carregamento
            const loadingUrl = `/carregando?tipo=${tipoTransicao}&redirect=${encodeURIComponent(href)}`;
            
            // Redirecionar para a página de carregamento
            window.location.href = loadingUrl;
        });
    });
});