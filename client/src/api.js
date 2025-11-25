const API = "http://localhost:6660/api";
let id = null;
let channelRegistered = false;
let eventSource = null;

async function listAuctions() {
    fetch(`${API}/leiloes`).then(response => {
        if (!response.ok) {
            throw new Error("Erro ao buscar leilões");
        }
        return response.json();
    })
    .then(data => {
        const div = document.getElementById("auctions-list");
        div.innerHTML = "";
        if (data.length === 0) {
            div.innerHTML += `
                    Nenhum leilão encontrado.
                `;
        }
        else {
            data.forEach(auction => {
                div.innerHTML += `
                    <div style="padding:10px; border-bottom:1px solid #ccc;">
                        <strong>ID:</strong> ${auction.id}<br>
                        <strong>Descrição:</strong> ${auction.description}<br>
                        <strong>Início:</strong> ${new Date(auction.start_date).toLocaleString()}<br>
                        <strong>Fim:</strong> ${new Date(auction.end_date).toLocaleString()}<br>
                        <strong>Status:</strong> ${auction.status}
                    </div>
                `;
            });
        }
    })
    .catch(error => {
        console.error("Erro:", error)
    })
}

async function createAuction() {
    const description = document.getElementById("description").value;

    const startValue = parseInt(document.getElementById("start-in-value").value);
    const startUnit = document.getElementById("start-in-unit").value;

    const durationValue = parseInt(document.getElementById("duration-value").value);
    const durationUnit = document.getElementById("duration-unit").value;

    if (!description) {
        alert("Insira uma descrição!");
        return;
    }

    if (isNaN(startValue) || isNaN(durationValue)) {
        alert("Insira valores numéricos válidos!");
        return;
    }

    const body = {
        description: description,
        start_in: { [startUnit]: startValue },
        duration: { [durationUnit]: durationValue }
    };

    await fetch(`${API}/leiloes`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(body)
    });

    document.getElementById("description").value = "";

    document.getElementById("start-in-value").value = "";
    document.getElementById("start-in-unit").selectedIndex = 0;

    document.getElementById("duration-value").value = "";
    document.getElementById("duration-unit").selectedIndex = 0;
    listAuctions()
}

async function makeBid() {

    const auctionId = document.getElementById("auction-id").value;
    const userId = id;
    const value = parseFloat(document.getElementById("bid-value").value);

    const data = {
        auction_id: auctionId,
        user_id: userId,
        value: value
    };

    await fetch(`${API}/lances`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });

    document.getElementById("auction-id").value = "";
    document.getElementById("bid-value").value = "";
}

async function toggleChannel() {
    const userIdInput = document.getElementById("user-id");
    const userId = userIdInput.value;
    const btn = document.getElementById("channel-btn");

    if (!userId) {
        alert("Informe um ID de usuário!");
        return;
    }
    id = userId;

    if (!channelRegistered) {
        try {
            await fetch(`${API}/register_channel`, {
                method: "POST",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ user_id: id, channel: id })
            });
            startSSE(id);

            channelRegistered = true;
            btn.textContent = "Remover Canal SSE";
            btn.style.background = "#ff0000";
            userIdInput.disabled = true;
        } catch (err) {
            console.error('Erro ao registrar canal:', err);
            alert('Erro ao registrar canal SSE');
        }
    } else {
        if (eventSource) {
            eventSource.close();
            eventSource = null;
        }

        try {
            await fetch(`${API}/register_channel`, {
                method: "DELETE",
                headers: {"Content-Type": "application/json"},
                body: JSON.stringify({ user_id: id })
            });

            channelRegistered = false;
            btn.textContent = "Registrar Canal SSE";
            btn.style.background = "#0000ff";
            userIdInput.disabled = false;
        } catch (err) {
            console.error('Erro ao remover canal:', err);
        }
    }
}

async function registerInterest() {
    const data = {
        auction_id: document.getElementById("interested-auction").value,
        user_id: id
    };

    await fetch(`${API}/interest`, {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify(data)
    });
}

function startSSE(userId) {
    if (eventSource) {
        eventSource.close();
    }

    eventSource = new EventSource(`${API}/sse/${userId}`);

    eventSource.onopen = () => {
        console.log("SSE conectado para usuário", userId);
        notify("Conectado ao canal SSE");
    };

    eventSource.onerror = (err) => {
        console.error("Erro SSE:", err);
        notify("Erro na conexão SSE");
    };

    eventSource.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'heartbeat') {
                console.log("Heartbeat recebido");
                return;
            }
            notify("Mensagem: " + event.data);
        } catch (e) {
            console.log("Mensagem SSE:", event.data);
        }
    };



    eventSource.addEventListener("lance_valido", e => {
        const data = JSON.parse(e.data);
        notify(`Lance válido no leilão ${data.auction_id}: R$${data.value}`);
    });

    eventSource.addEventListener("lance_invalido", e => {
        const data = JSON.parse(e.data);
        notify(`Lance inválido no leilão ${data.auction_id}: R$${data.value}`);
    });

    eventSource.addEventListener("vencedor_leilao", e => {
        const data = JSON.parse(e.data);
        if (data.user_id == userId) {
            notify(`PARABÉNS! Você venceu o leilão ${data.auction_id} com R$${data.highest_bid}`);
        } else {
            notify(`Vencedor do leilão ${data.auction_id}: usuário ${data.user_id} com R$${data.highest_bid}`);
        }
    });

    eventSource.addEventListener("link_pagamento", e => {
        const data = JSON.parse(e.data);
        if (data.user_id == userId) {
            notify(`Link de pagamento: <a href="${data.payment_url}" target="_blank">Clique aqui para pagar R$${data.amount}</a>`);
        }
    });

    eventSource.addEventListener("status_pagamento", e => {
        const data = JSON.parse(e.data);
        if (data.user_id == userId) {
            const status = data.status === 'approved' ? 'APROVADO' : 'RECUSADO';
            notify(`Status do pagamento: ${status} (R$${data.amount})`);
        }
    });
}

function notify(msg) {
    const div = document.getElementById("notifications");
    div.innerHTML += `<div>→ ${msg}</div>`;
    div.scrollTop = div.scrollHeight;
}
