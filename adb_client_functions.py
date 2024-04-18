import subprocess
import time

import logger


class Adb:

    def set_wifi_enable(self):
        command = ['cmd /c adb shell cmd -w wifi set-wifi-enabled disabled',
                   'adb shell cmd -w wifi status',
                   'adb shell cmd -w wifi set-wifi-enabled enabled',
                   'adb shell cmd -w wifi status']

        for i in command:
            cmd = subprocess.Popen(i, shell=True, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE)  # start -- cmd visible, /c -- close cmd after execution
            if 'status' in i:
                wifi_status = cmd.communicate()
                if 'Wifi is enabled' in str(wifi_status[0]):
                    print('Mobile client Wifi is Enabled')
            time.sleep(5)

    def set_wifi_disable(self):
        command = ['cmd /c adb shell cmd -w wifi set-wifi-enabled enabled',
                   'adb shell cmd -w wifi status ',
                   'adb shell cmd -w wifi set-wifi-enabled disabled',
                   'adb shell cmd -w wifi status']

        for i in command:
            cmd = subprocess.Popen(i, shell=True, stdin=subprocess.PIPE,
                                   stdout=subprocess.PIPE)  # start -- cmd visible, /c -- close cmd after execution
            if 'status' in i:
                wifi_status = cmd.communicate()
                if 'Wifi is disabled' in str(wifi_status[0]):
                    print('Mobile client Wifi is disabled')
            time.sleep(5)

    def connect_ap(self, ap_ssid_='Default', ap_password_='12345678', ap_security_='wpa2'):

        result = 0
        if ap_security_ == 'wpa2':
            try:
                self.connect_wifi_security_wpa(ap_ssid_, ap_password_)
            except:
                try:
                    ap_password_element = []
                    for element in ap_password_:
                        ap_password_element.append(element)
                    for element in ap_password_element:
                        if element in ['(', ')', '&', '<', '>', '\\']:
                            print('Password has Special character')
                            ap_password_ = self.special_character_connect_password(ap_password_)
                            # print(ap_ssid_)
                            ap_password_element = []
                            for el in ap_password_:
                                ap_password_element.append(el)
                            break
                    for element in ap_password_element:
                        if element in [' ', '  ', '   ']:
                            print('Password has Spaces')
                            ap_password_element.insert(0, "'")
                            ap_password_element.insert(len(ap_password_element), "'")
                            ap_password_ = self.list_to_string(ap_password_element)
                            # print(ap_ssid_)
                            break
                    # print(ap_password_)
                    self.connect_wifi_security_wpa(ap_ssid_, ap_password_)
                except:
                    print('Client could not connect to ' + ap_ssid_)
                    exit()
        else:
            try:
                self.connect_wifi_security_none(ap_ssid_)
            except Exception as e:
                logger.error(f"Error connecting with no security: {e}")
                raise e

        try:
            self.check_ipv4_ping_connectivity()
            logger.info('IPv4 ping connectivity check passed')
        except Exception as e:
            logger.error(f"IPv4 ping connectivity check failed: {e}")
            try:
                self.set_wifi_disable()
                self.set_wifi_enable()
                time.sleep(5)
                self.check_ipv4_ping_connectivity()
                logger.info('IPv4 ping connectivity check passed after reset')
            except Exception as e:
                logger.error(f"IPv4 ping connectivity check failed even after reset: {e}")
                result += 1

        try:
            self.check_ipv6_ping_connectivity()
            logger.info('IPv6 ping connectivity check passed')
        except Exception as e:
            logger.error(f"IPv6 ping connectivity check failed: {e}")
            try:
                self.set_wifi_disable()
                self.set_wifi_enable()
                time.sleep(5)
                self.check_ipv6_ping_connectivity()
                logger.info('IPv6 ping connectivity check passed after reset')
            except Exception as e:
                logger.error(f"IPv6 ping connectivity check failed even after reset: {e}")
                result += 1

        if result == 0:
            logger.info('Ping tests passed, checking YouTube run')
            try:
                self.youtube_stats_compare()
                logger.info('YouTube run complete')
            except Exception as e:
                logger.error(f"YouTube stats compare failed: {e}")
                logger.error("Total number of packets transmitted and received are lesser than expected. "
                             "Please check internet access.")
                result += 1
        else:
            assert result == 0
        assert result == 0

    def youtube_stats_compare(self, link=None):
        if link is None:
            link = input.live_feed_link

        commands = [
            'cmd /c adb shell cmd -w wifi status',
            'adb shell am force-stop com.google.android.youtube',
            f'adb shell am start {link}',
            'adb shell am force-stop com.google.android.youtube',
            'adb shell cmd -w wifi status'
        ]

        try:
            old_transmit_packets = old_receive_packets = new_transmit_packets = new_receive_packets = 0
            count = 0

            for command in commands:
                cmd = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE)
                cmd_out, cmd_err = cmd.communicate()
                if cmd_err:
                    raise subprocess.CalledProcessError(cmd.returncode, command, cmd_out, cmd_err)

                if count == 0:
                    adb_shell_data_string = str(cmd_out)
                    adb_shell_data_string_split = adb_shell_data_string.split(',')
                    packets = adb_shell_data_string_split[-1].split('\\r\\n')
                    for data in packets:
                        packets_ = data.split(':')
                        if packets_[0] == 'successfulTxPackets':
                            old_transmit_packets = packets_[-1]
                            logger.info("Old Packet T : " + old_transmit_packets)
                        if packets_[0] == 'successfulRxPackets':
                            old_receive_packets = packets_[-1]
                            logger.info("Old Packet R : " + old_receive_packets)

                if count == 2:
                    time.sleep(120)

                if count == 4:
                    adb_shell_data_string = str(cmd_out)
                    adb_shell_data_string_split = adb_shell_data_string.split(',')
                    packets = adb_shell_data_string_split[-1].split('\\r\\n')
                    for data in packets:
                        packets_ = data.split(':')
                        if packets_[0] == 'successfulTxPackets':
                            new_transmit_packets = packets_[-1]
                            logger.info("New Packet T : " + new_transmit_packets)
                        if packets_[0] == 'successfulRxPackets':
                            new_receive_packets = packets_[-1]
                            logger.info("New Packet R : " + new_receive_packets)
                count += 1

            diff_transmit = int(new_transmit_packets) - int(old_transmit_packets)
            diff_receive = int(new_receive_packets) - int(old_receive_packets)
            assert (diff_transmit >= 800) and (diff_receive >= 800)
            logger.info("Transmit and receive packets difference meet the threshold.")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error executing command '{e.cmd}': {e}")
        except AssertionError:
            logger.error("Transmit and receive packets difference do not meet the threshold.")

    def check_ipv4_ping_connectivity(self):

        cmd = subprocess.Popen('cmd /c adb shell ping -c 60 www.google.com', shell=True,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_out, cmd_err = cmd.communicate(timeout=62)
        if cmd_err:
            raise subprocess.CalledProcessError(cmd.returncode, cmd.args, cmd_out, cmd_err)

        packets = []
        adb_shell_data_string = str(cmd_out)
        adb_shell_data_string_split = adb_shell_data_string.split(',')

        for element in adb_shell_data_string_split:
            if 'loss' in element:
                packets = element.split('\\r\\n')

        loss_packets = packets[0].split()
        loss = loss_packets[0].split('%')
        logger.info('Loss %= ' + str(loss))
        assert int(loss[0]) <= 10
        logger.info("Loss percentage meets the threshold.")

    def check_ipv6_ping_connectivity(self):

        cmd = subprocess.Popen('cmd /c adb shell ping6 -c 60 www.google.com', shell=True,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        cmd_out, cmd_err = cmd.communicate(timeout=62)
        if cmd_err:
            raise subprocess.CalledProcessError(cmd.returncode, cmd.args, cmd_out, cmd_err)

        packets = []
        adb_shell_data_string = str(cmd_out)
        adb_shell_data_string_split = adb_shell_data_string.split(',')

        for element in adb_shell_data_string_split:
            if 'loss' in element:
                packets = element.split('\\r\\n')

        loss_packets = packets[0].split()
        loss = loss_packets[0].split('%')
        logger.info('Loss %= ' + str(loss))
        assert int(loss[0]) <= 10
        logger.info("Loss percentage meets the threshold.")

    def list_to_string(self, s):
        str1 = ""
        for ele in s:
            str1 += str(ele)
        return str1

    def special_character_connect_ssid(self, ssid):
        ssid_list = []
        for i in range(len(ssid)):
            if ssid[i] in ['*', '(', ')', '&', '<', '>', '\\']:
                x = r'\'' + ssid[i]
                y = list(x)
                y.remove('\'')
                # print(x)
                # print(y)
                z = ''.join(y)
                #
                ssid_list.append(z)
                print(ssid_list)
            else:
                ssid_list.append(ssid[i])
        a = self.list_to_string(ssid_list)
        print(a)
        return a

    def special_character_connect_password(self, password_):
        password_list = []
        for i in range(len(password_)):
            if password_[i] in ['(', ')', '&', '<', '>', '\\']:
                x = r'\'' + password_[i]
                y = list(x)
                y.remove('\'')
                # print(x)
                # print(y)
                z = ''.join(y)
                #
                password_list.append(z)
                # print(password_list)
            else:
                password_list.append(password_[i])
        b = self.list_to_string(password_list)
        # print(b)
        return b

    def connect_wifi_security_wpa(self, ssid, password):

        connect = 0
        command = ['cmd -w wifi connect-network "' + ssid + '" wpa2 "' + password + '"', 'cmd -w wifi status']
        for i in command:
            cmd_execution = subprocess.Popen('adb shell', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            result = cmd_execution.communicate(bytes(i, 'utf-8'))
            time.sleep(30)
            # print(command)

        if 'status' in i:
            wifi_status = result
            #   print(wifi_status)
            wifi_status_list = str(wifi_status).split('\\r\\n')
            #   print(wifi_status_list)
            for data in wifi_status_list:
                if ssid and 'connected' in data:
                    #   print(data)
                    connect += 1
                    if 'Wifi is not connected' in data:
                        connect -= 1
            if connect == 1:
                print('Client is successfully connected to ' + ssid)
            else:
                print('Client is not connected to ' + ssid)
        assert connect == 1

    def connect_wifi_security_none(self, ssid_):
        connect = 0
        command = ['cmd -w wifi connect-network "' + ssid_ + '" open "' + '"', 'cmd -w wifi status']
        for i in command:
            cmd_execution = subprocess.Popen('adb shell', stdin=subprocess.PIPE, stdout=subprocess.PIPE)
            result = cmd_execution.communicate(bytes(i, 'utf-8'))
            time.sleep(30)

        if 'status' in i:
            wifi_status = result
            #   print(wifi_status)
            wifi_status_list = str(wifi_status).split('\\r\\n')
            #   print(wifi_status_list)
            for data in wifi_status_list:
                if ssid_ and 'connected' in data:
                    #   print(data)
                    connect += 1
                    if 'Wifi is not connected' in data:
                        connect -= 1
            if connect == 1:
                print('Client is successfully connected to ' + ssid_)
            else:
                print('Client is not connected to ' + ssid_)
        assert connect == 1



# __pycache__/firewall.cpython-310.pyc
# __pycache__/functional_sanity.cpython-310.pyc
# __pycache__/health_check.cpython-310.pyc
# __pycache__/input.cpython-310.pyc
# __pycache__/locaters.cpython-310.pyc
# __pycache__/logger.cpython-310.pyc
# __pycache__/login.cpython-310.pyc
# __pycache__/maintenance_functionalities.cpython-310.pyc
# __pycache__/setup.cpython-310.pyc
# __pycache__/utils.cpython-310.pyc
# __pycache__/wireless.cpython-310.pyc
# adb_client_functions.py
# input.py
# main.py

