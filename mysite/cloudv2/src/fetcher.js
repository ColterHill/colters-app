let cookieValue = `; ${document.cookie}`;
let cookieParts = cookieValue.split(`; csrftoken=`)
let csrf;
if (cookieParts.length === 2) csrf = cookieParts.pop().split(';').shift();

const fetcher = async (url, options={}) => {
    if (options.get) {
        options.method = 'GET';
        url = `${url}?${new URLSearchParams(options.get)}`;
        delete options.get;
    }
    else if (options.post) {
        options.method = 'POST';
        options.body = JSON.stringify(options.post);
        delete options.post;
    }
    else if (options.put) {
        options.method = 'PUT';
        options.body = JSON.stringify(options.put);
        delete options.put;
    }
    if (!options.method) options.method = 'GET';
    if (options.method == 'POST' || options.method == 'PUT') {
        options.headers = options.headers || {};
        options.headers['Content-Type'] = 'application/json';
        if (csrf) options.headers['X-CSRFToken'] = csrf;
        options.credentials = 'same-origin';
    }

    let resp = await fetch(url, options);
    return resp.json().then(res => res);
}

export default fetcher;