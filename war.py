"""
Nolan Charlton
Comp 332
war card game client and server
"""
import socket
import random
import sys

def create_deck():
    """""
    52 card deck creation and categorization
    """""
    suits = ["C", "D", "H", "S"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]
    return [rank + suit for suit in suits for rank in ranks]

def deal_cards(deck):
    """
    Random distribution of cards into two even decks
    """
    random.shuffle(deck)
    return deck[:26], deck[26:]

def handle_round(conn1, conn2, deck1, deck2):
    """
    One round of the game, exchanges and compares each players card, then updates both decks
    """
    conn1.send(deck1.pop(0).encode())
    conn2.send(deck2.pop(0).encode())
    card1 = conn1.recv(1024).decode()
    card2 = conn2.recv(1024).decode()

    if card1 and card2:
        rank1 = "23456789TJQKA".index(card1[0])
        rank2 = "23456789TJQKA".index(card2[0])

        if rank1 > rank2:
            deck1.extend([card1, card2])
            return 1
        elif rank2 > rank1:
            deck2.extend([card1, card2])
            return 2
        else:
            return handle_war(conn1, conn2, deck1, deck2)
    return 0

def handle_war(conn1, conn2, deck1, deck2):
    """
    Resolves the "War" condition with a 3 card duel
    """
    if len(deck1) < 4 or len(deck2) < 4:
        if len(deck1) <= len(deck2):
            deck2.extend(deck1)
            deck1.clear()
            return 2
        else:
            deck1.extend(deck2)
            deck2.clear()
            return 1

    conn1.send("WAR".encode())
    conn2.send("WAR".encode())

    war_cards1 = [deck1.pop(0) for _ in range(3)]
    war_cards2 = [deck2.pop(0) for _ in range(3)]

    conn1.send(deck1.pop(0).encode())
    conn2.send(deck2.pop(0).encode())
    card1 = conn1.recv(1024).decode()
    card2 = conn2.recv(1024).decode()

    if card1 and card2:
        rank1 = "23456789TJQKA".index(card1[0])
        rank2 = "23456789TJQKA".index(card2[0])

        if rank1 > rank2:
            deck1.extend(war_cards1 + war_cards2 + [card1, card2])
            return 1
        elif rank2 > rank1:
            deck2.extend(war_cards1 + war_cards2 + [card1, card2])
            return 2
        else:
            return handle_war(conn1, conn2, deck1, deck2)
    return 0

def run_server(host, port):
    """
    Starts the server, accepts two client connections, and runs the War game
    """
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(2)

    print(f"Server started on {host}:{port}, waiting for 2 players to connect...")

    conn1, addr1 = server_socket.accept()
    print(f"Player 1 connected from {addr1}")
    conn2, addr2 = server_socket.accept()
    print(f"Player 2 connected from {addr2}")

    deck = create_deck()
    deck1, deck2 = deal_cards(deck)

    conn1.send("Start".encode())
    conn2.send("Start".encode())

    round_max = 1000
    round_count = 0

    while deck1 and deck2 and round_count < round_max:
        round_count += 1
        winner = handle_round(conn1, conn2, deck1, deck2)

        if winner == 1:
            conn1.send("WIN".encode())
            conn2.send("LOSE".encode())
        elif winner == 2:
            conn1.send("LOSE".encode())
            conn2.send("WIN".encode())
        else:
            conn1.send("TIE".encode())
            conn2.send("TIE".encode())

    if round_count >= round_max:
        if len(deck1) > len(deck2):
            conn1.send("WINNER".encode())
            conn2.send("GAMEOVER".encode())
            print("Player 1 wins by card count!")
        elif len(deck2) > len(deck1):
            conn1.send("GAMEOVER".encode())
            conn2.send("WINNER".encode())
            print("Player 2 wins by card count!")
        else:
            conn1.send("DRAW".encode())
            conn2.send("DRAW".encode())
            print("Game ends in a draw!")
    elif not deck1:
        conn1.send("GAMEOVER".encode())
        conn2.send("WINNER".encode())
        print("Player 2 wins!")
    else:
        conn1.send("WINNER".encode())
        conn2.send("GAMEOVER".encode())
        print("Player 1 wins!")

    conn1.close()
    conn2.close()
    server_socket.close()

def run_client(host, port):
    """
    Connect client to server as a player and recieve outcome
    """
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    print("Connected to server. Waiting for game to start...")

    start_message = client_socket.recv(1024).decode()
    if start_message == "Start":
        while True:
            card = client_socket.recv(1024).decode()

            if card == "GAMEOVER":
                print("You lose!")
                break
            elif card == "WINNER":
                print("You win!")
                break
            elif card == "DRAW":
                print("Stalemate occured! The game ended in a draw!")
                break
            elif card == "TIE" or card == "WAR":
                continue
            else:
                client_socket.send(card.encode())
                result = client_socket.recv(1024).decode()
                if result == "WIN":
                    print("You win the round!")
                elif result == "LOSE":
                    print("You lose the round.")
                elif result == "TIE":
                    print("Round was a tie.")

    client_socket.close()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Please format as: python3 war_game.py server/client <host> <port>")
        sys.exit(1)

    role = sys.argv[1]
    host = sys.argv[2]
    try:
        port = int(sys.argv[3])
    except ValueError:
        print("Error: Port argument needs to be an integer.")
        sys.exit(1)

    if role == "server":
        run_server(host, port)
    elif role == "client":
        run_client(host, port)
    else:
        print("Error: First argument needs to be 'server' or 'client'.")
        sys.exit(1)