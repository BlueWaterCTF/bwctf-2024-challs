        function init(currentUser){
            const hash = decodeURI(window.location.hash.slice(1));
            if(hash != '')
                fetchAndDisplayBio(hash);
            else fetchAndDisplayBio(currentUser);
        }

        const dompurifyFrame = document.getElementById('dompurifyFrame');
        const updateForm = document.getElementById('updateBioForm');

        // Function to sanitize content using DOMPurify iframe
        function sanitize(content) {
            return new Promise((resolve) => {
                const channel = new MessageChannel();
                channel.port1.onmessage = (event) => {
                    resolve(event.data);
                    channel.port1.close();
                };
                dompurifyFrame.contentWindow.postMessage(content, '*', [channel.port2]);
            });
        }

        function fetchAndDisplayBio(username) {
            fetch('/user/' + username)
                .then(response => response.json())
                .then(data => sanitize(data.bio))
                .then(sanitizedBio => {
                    document.getElementById('userBio').innerHTML = sanitizedBio;
                })
                .catch(error => console.error('Error:', error));
        }

        // Check for username in URL hash
        function userUpdate() {
            const hash = decodeURI(window.location.hash.slice(1));
            fetchAndDisplayBio(hash);
        }

        // Update bio
        updateForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const bio = document.getElementById('bioInput').value;
            fetch('/user/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'bio=' + encodeURIComponent(bio)
            })
            .then(response => response.text())
            .then(() => sanitize(bio))
            .then(sanitizedBio => {
                document.getElementById('userBio').innerHTML = sanitizedBio;
            })
            .catch(error => console.error('Error:', error));
        });
