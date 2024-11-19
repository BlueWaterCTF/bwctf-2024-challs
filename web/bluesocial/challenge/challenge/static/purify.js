import '/static/dompurify.js';

window.addEventListener('message', function(event) {
    try{
        if (event.origin !== window.location.origin) return;

        var sanitizedContent = event.data; 
        sanitizedContent = DOMPurify.sanitize(event.data);
        event.ports[0].postMessage(sanitizedContent);
    }catch(error){
        event.ports[0].postMessage(sanitizedContent);
    }
}, false);
