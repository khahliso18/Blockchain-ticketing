import streamlit as st
import hashlib
import json
import time
from typing import List, Dict, Any

# -----------------------
# Blockchain Class
# -----------------------
class Blockchain:
    def __init__(self):
        self.chain: List[Dict[str, Any]] = []
        self.pending_tickets: List[Dict[str, Any]] = []
        self.ticket_counter = 0
        # Genesis block
        self.new_block(proof=100, previous_hash="1")

    def new_block(self, proof: int, previous_hash: str = None) -> Dict[str, Any]:
        block_tickets = [tx.copy() for tx in self.pending_tickets]
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "tickets": block_tickets,
            "proof": proof,
            "previous_hash": previous_hash or self.hash(self.chain[-1]),
        }
        self.pending_tickets = []
        block["hash"] = self.hash(block)
        self.chain.append(block)
        return block

    def new_ticket(self, buyer: str, event: str) -> int:
        """Generate a new ticket for buyer"""
        self.ticket_counter += 1
        ticket = {
            "ticket_id": self.ticket_counter,
            "event": event,
            "buyer": buyer,
            "timestamp": time.time(),
        }
        self.pending_tickets.append(ticket)
        return ticket["ticket_id"]

    @staticmethod
    def hash(block: Dict[str, Any]) -> str:
        block_copy = block.copy()
        block_copy.pop("hash", None)
        block_string = json.dumps(block_copy, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self) -> Dict[str, Any]:
        return self.chain[-1]

    def is_chain_valid(self) -> bool:
        for i in range(1, len(self.chain)):
            prev = self.chain[i - 1]
            curr = self.chain[i]
            if curr["previous_hash"] != prev["hash"]:
                return False
            if curr["hash"] != self.hash(curr):
                return False
        return True

    def verify_ticket(self, ticket_id: int) -> Dict[str, Any]:
        """Check if a ticket exists and is valid"""
        for block in self.chain:
            for ticket in block["tickets"]:
                if ticket["ticket_id"] == ticket_id:
                    return {
                        "valid": True,
                        "ticket_id": ticket_id,
                        "event": ticket["event"],
                        "buyer": ticket["buyer"],
                        "block_index": block["index"],
                    }
        return {"valid": False}


# -----------------------
# Streamlit App
# -----------------------
st.set_page_config(page_title="🎟️ Blockchain Ticketing System", layout="wide")

# Initialize blockchain
if "blockchain" not in st.session_state:
    st.session_state.blockchain = Blockchain()

bc: Blockchain = st.session_state.blockchain

st.title("🎟️ Blockchain-based Event Ticketing System")

# Status
col1, col2 = st.columns(2)
col1.metric("Chain Length", len(bc.chain))
col2.metric("Is Chain Valid?", "✅ Yes" if bc.is_chain_valid() else "❌ No")

# --- Buy Ticket ---
st.header("🛒 Buy Ticket")
with st.form("buy_form", clear_on_submit=True):
    buyer = st.text_input("Buyer Name")
    event = st.text_input("Event Name")
    submitted = st.form_submit_button("Purchase Ticket")
    if submitted and buyer and event:
        ticket_id = bc.new_ticket(buyer, event)
        block = bc.new_block(proof=123)
        st.success(
            f"✅ Ticket #{ticket_id} purchased by {buyer} for {event}. "
            f"Added in Block {block['index']}."
        )

# --- Verify Ticket ---
st.header("🔍 Verify Ticket")
verify_id = st.number_input("Enter Ticket ID", min_value=1, step=1)
if st.button("Check Ticket"):
    result = bc.verify_ticket(verify_id)
    if result["valid"]:
        st.success(
            f"🎟️ Ticket #{result['ticket_id']} is VALID!\n\n"
            f"- Event: {result['event']}\n"
            f"- Buyer: {result['buyer']}\n"
            f"- Block: {result['block_index']}"
        )
    else:
        st.error(f"❌ Ticket #{verify_id} is INVALID or does not exist.")

# --- Explorer ---
st.header("📜 Blockchain Explorer")
for block in reversed(bc.chain):
    with st.expander(f"Block {block['index']} (Hash: {block['hash'][:12]}...)"):
        st.write("Previous Hash:", block.get("previous_hash"))
        st.write("Hash:", block.get("hash"))
        st.json(block.get("tickets", []))
