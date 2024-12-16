import time
import settings
import config_manager
import display_manager
import interface_manager
import network_manager


def main():
    print("STARTING")
    try:
        settings = settings.Settings()
        config_mng = config_manager.ConfigManager(settings)
        config_mng.update_config()
        config = config_mng.load_config_file()
        image_processor = config_mng.get_image_processor()
        network_mng = network_manager.NetworkManager(settings)

        display_mng = display_manager.DisplayManager(settings, image_processor)
        display_mng.show_info(config, network_mng)
        time.sleep(5)
        display_mng.epd.Clear()

        interface_mng = interface_manager.InterfaceManager(settings)

        rnd = False
        cur_image = 0
        last_network = 0
        last_update_image = 0
        mode = 0
        refresh_rate = 60

        if 'mode' in config and config['mode']:
            mode = config['mode']
        if 'random' in config and config['random']:
                    rnd = True
        if 'refresh_rate' in config and config['refresh_rate']:
            refresh_rate = config['refresh_rate']

        while True:  

            if mode == 4: # TD
                network_mng.receive_frame(display_mng.epd)
            else:
                if refresh_rate > 0:
                    if last_update_image < time.time():
                        if mode == 0: # BASIC
                            cur_image, last_update_image = display_manager.show_next_image(cur_image, 'images', config, last_update_image, rnd)
                        elif mode == 1: # NET
                            if last_network < time.time():
                                last_network, last_update_image = display_manager.show_netimage(config, last_network, last_update_image)
                            else:
                                cur_image, last_update_image = display_manager.show_next_image(cur_image, 'images', config, last_update_image, rnd)
                        elif mode == 2:
                            if last_network < time.time():
                                last_network, last_update_image = display_manager.show_netimage(config, last_network, last_update_image)
                            else:
                                cur_image, last_update_image = display_manager.show_next_image(cur_image, settings.specific_folder, config, last_update_image, rnd)
                        elif mode == 3: # SYNC
                            pass
            
            mode, last_update_image = interface_mng.read_button(mode, last_update_image, network_mng, display_mng)
            time.sleep(0.01)

    except IOError as e:
        print(e)

    except KeyboardInterrupt:
        print("ctrl + c:")
        display_manager.exit()
        interface_manager.exit()
        exit()

if __name__ == '__main__':
    main()