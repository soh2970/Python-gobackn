import time
import threading
import queue

class GBN_sender:
    def __init__(self, input_file, window_size, packet_len, nth_packet, send_queue, ack_queue, timeout_interval, logger):
        self.input_file = input_file
        self.window_size = window_size
        self.packet_len = packet_len
        self.nth_packet = nth_packet
        self.send_queue = send_queue
        self.ack_queue = ack_queue
        self.timeout_interval = timeout_interval
        self.logger = logger
        
        self.base = 0
        self.packets = []
        self.acks_list = []
        self.packet_timers = []
        self.dropped_list = []
        self.packet_drop_counter = nth_packet
        
        self.prepare_packets()
        self.acks_list = [False] * len(self.packets)
        self.packet_timers = [0] * len(self.packets)

    def prepare_packets(self):
        try:
            with open(self.input_file, 'r') as f:
                data = f.read()
            
            binary_data = ''.join(format(ord(c), '08b') for c in data)
            
            data_size = self.packet_len - 16
            
            packets = []  
            
            for i in range(0, len(binary_data), data_size):
                chunk = binary_data[i:i + data_size]
                if len(chunk) < data_size:
                    chunk = chunk.ljust(data_size, '0')
                sequence_number = format(len(packets), '016b')
                packet = chunk + sequence_number
                packets.append(packet)
            
            self.packets = packets
            self.acks_list = [False] * len(packets)  
            self.packet_timers = [0] * len(packets)  
            self.dropped_list = []  
            
            self.logger.info(f"{len(self.packets)} packets created, Window size: {self.window_size}, "
                            f"Packet length: {self.packet_len}, Nth packet to be dropped: {self.nth_packet}, "
                            f"Timeout interval: {self.timeout_interval}")
            
            return packets  
        except Exception as e:
            self.logger.error(f"Error preparing packets: {e}")

    def send_packets(self):
        for i in range(self.base, min(self.base + self.window_size, len(self.packets))):
            if not self.acks_list[i]:
                self.packet_drop_counter -= 1
                if self.packet_drop_counter == 0:
                    self.dropped_list.append(i) 
                    self.logger.info(f"Sender: packet {i} dropped")
                    self.packet_drop_counter = self.nth_packet
                else:
                    self.logger.info(f"sending packet {i} ")
                    self.send_queue.put(self.packets[i])
                    self.packet_timers[i] = time.time()

    def send_next_packet(self):
        self.base += 1
        if self.base < len(self.packets):
            next_packet = self.base + self.window_size - 1
            if next_packet < len(self.packets) and not self.acks_list[next_packet]:
                self.packet_drop_counter -= 1
                if self.packet_drop_counter == 0:
                    self.dropped_list.append(next_packet)
                    self.logger.info(f"Sender: packet {next_packet} dropped")
                    self.packet_drop_counter = self.nth_packet
                else:
                    self.send_queue.put(self.packets[next_packet])
                    self.packet_timers[next_packet] = time.time()
                    self.logger.info(f"sending packet {next_packet}")

    def check_timers(self):
        current_time = time.time()
        for i in range(self.base, min(self.base + self.window_size, len(self.packets))):
            if not self.acks_list[i] and (current_time - self.packet_timers[i]) > self.timeout_interval:
                self.logger.info(f"Sender: packet {i} timed out")
                self.send_queue.put(self.packets[i])
                self.packet_timers[i] = time.time()
                self.logger.info(f"Sender: packet {i} retransmitted due to timeout")

    def receive_acks(self):
        while True:
            try:
                ack = self.ack_queue.get(timeout=0.1)
                if ack is None:
                    break
                if ack < len(self.acks_list) and not self.acks_list[ack]:
                    self.acks_list[ack] = True
                    self.logger.info(f"Sender: ack {ack} received")
                    while self.base < len(self.acks_list) and self.acks_list[self.base]:
                        self.send_next_packet()
                elif ack < len(self.acks_list):
                    self.logger.info(f"Sender: ack {ack} received, Ignoring")
            except queue.Empty:
                continue

    def run(self):
        try:
            self.send_packets()
            ack_thread = threading.Thread(target=self.receive_acks)
            ack_thread.start()
            
            while self.base < len(self.packets):
                self.check_timers()
                time.sleep(0.1)
            
            self.send_queue.put(None)
            ack_thread.join()
        except Exception as e:
            self.logger.error(f"Error in sender run: {e}")


class GBN_receiver:
    def __init__(self, output_file, send_queue, ack_queue, logger):
        self.output_file = output_file
        self.send_queue = send_queue
        self.ack_queue = ack_queue
        self.logger = logger
        self.expected_seq_num = 0
        self.packet_list = []

    def process_packet(self, packet):
        try:
            sequence_number = int(packet[-16:], 2)
            data = packet[:-16]
            if sequence_number == self.expected_seq_num:
                self.packet_list.append(data)
                self.logger.info(f"Receiver: packet {sequence_number} received")
                self.ack_queue.put(sequence_number)
                self.expected_seq_num += 1
                return True
            else:
                self.logger.info(f"Receiver: packet {sequence_number} received out of order")
                if self.expected_seq_num > 0:
                    self.ack_queue.put(self.expected_seq_num - 1)
                return False
        except Exception as e:
            self.logger.error(f"Error processing packet: {e}")
            return False

    def write_to_file(self):
        try:
            binary_data = ''.join(self.packet_list)
            ascii_string = ''
            for i in range(0, len(binary_data), 8):
                byte = binary_data[i:i+8]
                if byte: 
                    ascii_string += chr(int(byte, 2))
            
            with open(self.output_file, 'w') as f:
                f.write(ascii_string)
        except Exception as e:
            self.logger.error(f"Error writing to file: {e}")

    def run(self):
        try:
            while True:
                packet = self.send_queue.get()
                
                if packet is None:
                    break
                    
                self.process_packet(packet)
                
            self.write_to_file()
        except Exception as e:
            self.logger.error(f"Error in receiver run: {e}")
