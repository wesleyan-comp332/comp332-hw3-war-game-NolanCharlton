import socket
import random

def create_deck():
    suits = ["Hearts", "Diamonds", "Clubs", "Spades"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
    deck = [f"{rank} of {suit}" for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck

def deal_cards(deck):
    return deck[:len(deck) // 2], deck[len(deck) // 2:]

def play_round(client_socket, player_deck):
    card = player_deck.pop()
    client_socket.send(card.encode())
    opponent_card = client_socket.recv(1024).decode()
    return card, opponent_card

def determine_winner(card1, card2):
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King", "Ace"]
    rank1 = ranks.index(card1.split()[0])
    rank2 = ranks.index(card2.split()[0])
    if rank1 > rank2:
        return 1
    elif rank2 > rank1:
        return 2
    else:
        return 0

def handle_client(client_socket, player_deck):
    while player_deck:
        card, opponent_card = play_round(client_socket, player_deck)
        result = determine_winner(card, opponent_card)
        if result == 1:
            player_deck.insert(0, card)
            player_deck.insert(0, opponent_card)
            client_socket.send("Won".encode())
        elif result == 2:
            client_socket.send("Lost".encode())
        else:
            client_socket.send("War".encode())
            war_cards1 = [player_deck.pop() for _ in range(min(3, len(player_deck)))]
            client_socket.send(','.join(war_cards1).encode())
            war_cards2_str = client_socket.recv(1024).decode()
            war_cards2 = war_cards2_str.split(',')
            if war_cards2_str:
              result = determine_winner(war_cards1[-1], war_cards2[-1])
              if result == 1:
                  player_deck.extend([card, opponent_card] + war_cards1 + war_cards2)
                  client_socket.send("Won War".encode())
              elif result == 2:
                  client_socket.send("Lost War".encode())
              else:
                  player_deck.extend([card, opponent_card] + war_cards1 + war_cards2)
                  client_socket.send("Tie War".encode())
            else:
                client_socket.send("Not Enough Cards".encode())
                break

        status = client_socket.recv(1024).decode()
        if status == "Opponent disconnected" or status == "Opponent has no cards":
            break

    if not player_deck:
      client_socket.send("You won!".encode())
    else:
      client_socket.send("You lost!".encode())
    client_socket.close()

def server_program():
    host = "127.0.0.1"
    port = 12345
    server_socket = socket.socket()
    server_socket.bind((host, port))
    server_socket.listen(2)
    clients = []
    for _ in range(2):
        client_socket, address = server_socket.accept()
        clients.append(client_socket)
        print(f"Connection from: {address}")

    deck = create_deck()
    player1_deck, player2_deck = deal_cards(deck)
    handle_client(clients[0], player1_deck)
    handle_client(clients[1], player2_deck)
    server_socket.close()

def client_program():
    host = "127.0.0.1"
    port = 12345
    client_socket = socket.socket()
    try:
      client_socket.connect((host, port))
    except ConnectionRefusedError:
      print("Server is not running. Please start the server first.")
      return

    player_deck = []
    while True:
        card_str = client_socket.recv(1024).decode()
        if not card_str:
            break
        if card_str in ["Won", "Lost", "War", "Won War", "Lost War", "Tie War", "Not Enough Cards", "You won!", "You lost!"]:
            if card_str in ["You won!", "You lost!"]:
              print(card_str)
              break
        else:
            player_deck.append(card_str)
            client_socket.send(player_deck[-1].encode())
            status = client_socket.recv(1024).decode()
            if status == "War":
                war_cards_str = client_socket.recv(1024).decode()
                if war_cards_str:
                    war_cards = war_cards_str.split(',')
                    war_cards_to_send = [player_deck.pop() for _ in range(min(3, len(player_deck)))]
                    client_socket.send(','.join(war_cards_to_send).encode())
                    war_status = client_socket.recv(1024).decode()
                    if war_status == "Not Enough Cards":
                        client_socket.send("Opponent has no cards".encode())
                        break
                else:
                    client_socket.send("Not Enough Cards".encode())
                    client_socket.send("Opponent disconnected".encode())
                    break
            if not player_deck:
                client_socket.send("Opponent has no cards".encode())
                break
            else:
              client_socket.send("OK".encode())
    client_socket.close()

if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'server':
        server_program()
    else:
        client_program()