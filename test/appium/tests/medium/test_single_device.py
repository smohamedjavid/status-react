import re
import random
import string

from tests import marks, mailserver_ams, mailserver_gc, mailserver_hk, used_fleet, common_password, test_dapp_name,\
    test_dapp_url, pair_code, unique_password
from tests.users import user_mainnet, chat_users, dummy_user, recovery_users, transaction_senders, basic_user,\
    wallet_users, ens_user_ropsten, ens_user
from selenium.common.exceptions import NoSuchElementException

from tests.base_test_case import SingleDeviceTestCase, MultipleDeviceTestCase
from views.send_transaction_view import SendTransactionView
from views.chat_view import ChatView
from views.sign_in_view import SignInView


@marks.medium
class TestChatManagement(SingleDeviceTestCase):

    @marks.testrail_id(6213)
    # TODO: check main e2e about block; may be it makes sense to add additional check to it and remove this e2e at all
    def test_contacts_unblock_user_is_not_added_back_to_contacts(self):
        home = SignInView(self.driver).create_user()
        chat = home.add_contact(basic_user["public_key"], add_in_contacts=False)

        chat.just_fyi('Block user not added as contact from chat view')
        chat.chat_options.click()
        chat.view_profile_button.click()
        chat.block_contact()
        chat.get_back_to_home_view()

        chat.just_fyi('Unblock user not added as contact from chat view')
        profile = home.profile_button.click()
        profile.contacts_button.click()
        profile.blocked_users_button.click()
        profile.element_by_text(basic_user["username"]).click()
        chat.unblock_contact_button.click()

        profile.just_fyi('Navigating to contact list and check that user is not in list')
        profile.close_button.click()
        profile.back_button.click()
        if profile.element_by_text(basic_user["username"]).is_element_displayed():
            self.driver.fail("Unblocked user not added previously in contact list added in contacts!")

    @marks.testrail_id(6319)
    # TODO: merge with other 1-driver medium e2e
    def test_permissions_deny_access_camera_and_gallery(self):
        home = SignInView(self.driver).create_user()
        general_camera_error = home.element_by_translation_id("camera-access-error")

        home.just_fyi("Denying access to camera in universal qr code scanner")
        home.plus_button.click()
        home.universal_qr_scanner_button.click()
        home.deny_button.click()
        general_camera_error.wait_for_visibility_of_element(3)
        home.ok_button.click()
        home.get_back_to_home_view()

        home.just_fyi("Denying access to camera in scan chat key view")
        home.plus_button.click()
        chat = home.start_new_chat_button.click()
        chat.scan_contact_code_button.click()
        chat.deny_button.click()
        general_camera_error.wait_for_visibility_of_element(3)
        chat.ok_button.click()
        home.get_back_to_home_view()

        home.just_fyi("Denying access to gallery at attempt to send image")
        home.add_contact(basic_user['public_key'])
        chat.show_images_button.click()
        chat.deny_button.click()
        chat.element_by_translation_id("external-storage-denied").wait_for_visibility_of_element(3)
        chat.ok_button.click()

        home.just_fyi("Denying access to audio at attempt to record audio")
        chat.audio_message_button.click()
        chat.deny_button.click()
        chat.element_by_translation_id("audio-recorder-permissions-error").wait_for_visibility_of_element(3)
        chat.ok_button.click()
        home.get_back_to_home_view()

        home.just_fyi("Denying access to camera in wallet view")
        wallet = home.wallet_button.click()
        wallet.scan_qr_button.click()
        wallet.deny_button.click()
        general_camera_error.wait_for_visibility_of_element(3)
        wallet.ok_button.click()

        home.just_fyi("Denying access to camera in send transaction > scan address view")
        wallet.accounts_status_account.click()
        send_transaction = wallet.send_transaction_button.click()
        send_transaction.chose_recipient_button.scroll_and_click()
        send_transaction.scan_qr_code_button.click()
        send_transaction.deny_button.click()
        general_camera_error.wait_for_visibility_of_element(3)
        send_transaction.ok_button.click()
        wallet.close_button.click()
        wallet.close_send_transaction_view_button.click()

        home.just_fyi("Allow access to camera in universal qr code scanner and check it in other views")
        wallet.home_button.click()
        home.plus_button.click()
        home.universal_qr_scanner_button.click()
        home.allow_button.click()
        if not home.element_by_text('Scan QR code').is_element_displayed():
            self.errors.append('Scan QR code is not opened after denying and allowing permission to the camera')
        home.cancel_button.click()
        wallet = home.wallet_button.click()
        wallet.scan_qr_button.click()
        if not home.element_by_text('Scan QR code').is_element_displayed():
            self.errors.append(
                'Scan QR code is not opened after allowing permission to the camera from univesal QR code'
                ' scanner view')
        wallet.cancel_button.click()
        wallet.home_button.click()
        home.get_chat(basic_user['username']).click()
        chat.show_images_button.click()
        chat.allow_button.click()
        if not chat.first_image_from_gallery.is_element_displayed():
            self.errors.append('Image previews are not shown after denying and allowing access to gallery')
        self.errors.verify_no_errors()

    @marks.testrail_id(6635)
    # TODO: merge with other 1-driver medium e2e
    def test_permissions_webview_camera(self):
        web_view_camera_url = 'https://simpledapp.status.im/webviewtest/webviewcamera.html'
        home = SignInView(self.driver).create_user()
        self.driver.set_clipboard_text(web_view_camera_url)
        dapp = home.dapp_tab_button.click()
        dapp.enter_url_editbox.click()
        dapp.paste_text()
        dapp.confirm()

        from views.web_views.base_web_view import BaseWebView
        camera_dapp = BaseWebView(self.driver)
        camera_dapp.just_fyi("Check camera request blocked (because it's not enabled in app yet)")
        camera_request_blocked = home.get_translation_by_key("page-camera-request-blocked")
        if not dapp.element_by_text_part(camera_request_blocked).is_element_displayed():
            self.driver.fail("There is no pop-up notifying that camera access need to be granted in app")
        camera_dapp.swipe_down()
        if not camera_dapp.camera_image_in_dapp.is_element_image_similar_to_template('blank_camera_image.png'):
            self.driver.fail("Even camera permissions not allowed - acccess to camera granted")

        profile = home.profile_button.click()
        profile.privacy_and_security_button.click()

        camera_dapp.just_fyi("Enable camera requests in Dapps")
        profile.element_by_translation_id("webview-camera-permission-requests").scroll_and_click()
        home.dapp_tab_button.click(desired_element_text='webview')

        camera_dapp.just_fyi("Check DApp asks now to allow camera aceess but Deny in DApp")
        camera_dapp.browser_refresh_page_button.click()
        camera_dapp.deny_button.click()
        if not camera_dapp.camera_image_in_dapp.is_element_image_similar_to_template('blank_camera_image.png'):
            self.driver.fail("Even camera access Denied to Dapp, - acccess to camera granted")

        camera_dapp.just_fyi("Check DApp asks now to allow camera aceess and Allow access to DApp")
        camera_dapp.browser_refresh_page_button.click()
        camera_dapp.allow_button.click()
        if camera_dapp.camera_image_in_dapp.is_element_image_similar_to_template('blank_camera_image.png'):
            self.driver.fail("Even camera access Accepted to Dapp, - camera view is not shown")

        camera_dapp.just_fyi("Relogin and check camera access still needs to be allowed")
        home.profile_button.click()
        profile.relogin()
        home.dapp_tab_button.click()
        camera_dapp.open_tabs_button.click()
        dapp.element_by_text_part("https").click()
        if not camera_dapp.allow_button.is_element_displayed():
            self.driver.fail("No request to camera access after relogin")

    @marks.testrail_id(6300)
    @marks.skip
    # TODO: waiting mode (rechecked 23.11.21, valid)
    def test_webview_security(self):
        home_view = SignInView(self.driver).create_user()
        daap_view = home_view.dapp_tab_button.click()

        browsing_view = daap_view.open_url('https://simpledapp.status.im/webviewtest/url-spoof-ssl.html')
        browsing_view.url_edit_box_lock_icon.click()
        if not browsing_view.element_by_translation_id("browser-not-secure").is_element_displayed():
            self.errors.append("Broken certificate displayed as secure connection \n")

        browsing_view.cross_icon.click()
        daap_view.open_url('https://simpledapp.status.im/webviewtest/webviewtest.html')
        browsing_view.element_by_text_part('204').click()
        if browsing_view.element_by_text_part('google.com').is_element_displayed():
            self.errors.append("URL changed on attempt to redirect to no-content page \n")

        browsing_view.cross_icon.click()
        daap_view.open_url('https://simpledapp.status.im/webviewtest/webviewtest.html')
        browsing_view.element_by_text_part('XSS check').click()
        browsing_view.open_in_status_button.click()
        if browsing_view.element_by_text_part('simpledapp.status.im').is_element_displayed():
            self.errors.append("XSS attemp succedded \n")
            browsing_view.ok_button.click()

        browsing_view.cross_icon.click()
        daap_view.open_url('https://simpledapp.status.im/webviewtest/url-blank.html')
        if daap_view.edit_url_editbox.text == '':
            self.errors.append("Blank URL value. Must show the actual URL \n")

        browsing_view.cross_icon.click()
        daap_view.open_url('https://simpledapp.status.im/webviewtest/port-timeout.html')
        # wait up  ~2.5 mins for port time out
        if daap_view.element_by_text_part('example.com').is_element_displayed(150):
            self.errors.append("URL spoof due to port timeout \n")

        self.errors.verify_no_errors()

    @marks.testrail_id(6298)
    # TODO: merge with other 1-driver medium e2e
    def test_scan_qr_with_scan_contact_code_via_start_chat(self):
        sign_in = SignInView(self.driver)
        home = sign_in.recover_access(basic_user['passphrase'])

        url_data = {
            'ens_with_stateofus_domain_deep_link': {
                'url': 'https://join.status.im/u/%s.stateofus.eth' % ens_user_ropsten['ens'],
                'username': '@%s' % ens_user_ropsten['ens']
            },
            'ens_without_stateofus_domain_deep_link': {
                'url': 'https://join.status.im/u/%s' % ens_user_ropsten['ens'],
                'username': '@%s' % ens_user_ropsten['ens']
            },
            'ens_another_domain_deep_link': {
                'url': 'status-im://u/%s' % ens_user['ens_another'],
                'username': '@%s' % ens_user['ens_another']
            },
            'own_profile_key_deep_link': {
                'url': 'https://join.status.im/u/%s' % basic_user['public_key'],
                'error': "That's you"
            },
            'other_user_profile_key_deep_link': {
                'url': 'https://join.status.im/u/%s' % transaction_senders['M']['public_key'],
                'username': transaction_senders['M']['username']
            },
            'other_user_profile_key_deep_link_invalid': {
                'url': 'https://join.status.im/u/%sinvalid' % ens_user['public_key'],
                'error': 'Please enter or scan a valid chat key'
            },
            'own_profile_key': {
                'url': basic_user['public_key'],
                'error': "That's you"
            },
            # 'ens_without_stateofus_domain': {
            #     'url': ens_user['ens'],
            #     'username': ens_user['username']
            # },
            'other_user_profile_key': {
                'url': transaction_senders['M']['public_key'],
                'username': transaction_senders['M']['username']
            },
            'other_user_profile_key_invalid': {
                'url': '%s123' % ens_user['public_key'],
                'error': 'Please enter or scan a valid chat key'
            },
        }

        for key in url_data:
            home.plus_button.click_until_presence_of_element(home.start_new_chat_button)
            contacts = home.start_new_chat_button.click()
            sign_in.just_fyi('Checking scanning qr for "%s" case' % key)
            contacts.scan_contact_code_button.click()
            if contacts.allow_button.is_element_displayed():
                contacts.allow_button.click()
            contacts.enter_qr_edit_box.scan_qr(url_data[key]['url'])
            from views.chat_view import ChatView
            chat = ChatView(self.driver)
            if url_data[key].get('error'):
                if not chat.element_by_text_part(url_data[key]['error']).is_element_displayed():
                    self.errors.append('Expected error %s is not shown' % url_data[key]['error'])
                chat.ok_button.click()
            if url_data[key].get('username'):
                if not chat.chat_message_input.is_element_displayed():
                    self.errors.append(
                        'In "%s" case chat input is not found after scanning, so no redirect to 1-1' % key)
                if not chat.element_by_text(url_data[key]['username']).is_element_displayed():
                    self.errors.append('In "%s" case "%s" not found after scanning' % (key, url_data[key]['username']))
                chat.get_back_to_home_view()
        self.errors.verify_no_errors()

    @marks.testrail_id(6322)
    # TODO: merge with other 1-driver medium e2e
    def test_scan_qr_different_links_with_universal_qr_scanner(self):
        user = transaction_senders['ETH_STT_3']
        home = SignInView(self.driver).recover_access(user['passphrase'])
        wallet = home.wallet_button.click()
        wallet.home_button.click()
        send_transaction = SendTransactionView(self.driver)

        url_data = {
            'ens_without_stateofus_domain_deep_link': {
                'url': 'https://join.status.im/u/%s' % ens_user_ropsten['ens'],
                'username': '@%s' % ens_user_ropsten['ens']
            },

            'other_user_profile_key_deep_link': {
                'url': 'status-im://u/%s' % basic_user['public_key'],
                'username': basic_user['username']
            },
            'other_user_profile_key_deep_link_invalid': {
                'url': 'https://join.status.im/u/%sinvalid' % ens_user['public_key'],
                'error': 'Unable to read this code'
            },
            'own_profile_key': {
                'url': user['public_key'],
            },
            'other_user_profile_key': {
                'url': transaction_senders['A']['public_key'],
                'username': transaction_senders['A']['username']
            },
            'wallet_validation_wrong_address_transaction': {
                'url': 'ethereum:0x744d70fdbe2ba4cf95131626614a1763df805b9e@3/transfer?address=blablabla&uint256=1e10',
                'error': 'Invalid address',
            },
            'wallet_eip_ens_for_receiver': {
                'url': 'ethereum:0xc55cf4b03948d7ebc8b9e8bad92643703811d162@3/transfer?address=nastya.stateofus.eth&uint256=1e-1',
                'data': {
                    'asset': 'STT',
                    'amount': '0.1',
                    'address': '0x58d8…F2ff',
                },
            },
            'wallet_eip_payment_link': {
                'url': 'ethereum:pay-0xc55cf4b03948d7ebc8b9e8bad92643703811d162@3/transfer?address=0x3d597789ea16054a084ac84ce87f50df9198f415&uint256=1e1',
                'data': {
                    'amount': '10',
                    'asset': 'STT',
                    'address': '0x3D59…F415',
                },
            },
            'dapp_deep_link': {
                'url': 'https://join.status.im/b/simpledapp.eth',
            },
            'dapp_deep_link_https': {
                'url': 'https://join.status.im/b/https://simpledapp.eth',
            },
            'public_chat_deep_link': {
                'url': 'https://join.status.im/baga-ma-2020',
                'chat_name': 'baga-ma-2020'
            },
        }

        for key in url_data:
            home.plus_button.click_until_presence_of_element(home.start_new_chat_button)
            home.just_fyi('Checking %s case' % key)
            if home.universal_qr_scanner_button.is_element_displayed():
                home.universal_qr_scanner_button.click()
            if home.allow_button.is_element_displayed():
                home.allow_button.click()
            home.enter_qr_edit_box.scan_qr(url_data[key]['url'])
            from views.chat_view import ChatView
            chat = ChatView(self.driver)
            if key == 'own_profile_key':
                from views.profile_view import ProfileView
                profile = ProfileView(self.driver)
                if not profile.default_username_text.is_element_displayed():
                    self.errors.append('In %s case was not redirected to own profile' % key)
                home.home_button.double_click()
            if url_data[key].get('error'):
                if not chat.element_by_text_part(url_data[key]['error']).is_element_displayed():
                    self.errors.append('Expected error %s is not shown' % url_data[key]['error'])
                chat.ok_button.click()
            if url_data[key].get('username'):
                if not chat.element_by_text(url_data[key]['username']).is_element_displayed():
                    self.errors.append('In %s case username not shown' % key)
            if 'wallet' in key:
                if url_data[key].get('data'):
                    actual_data = send_transaction.get_values_from_send_transaction_bottom_sheet()
                    difference_in_data = url_data[key]['data'].items() - actual_data.items()
                    if difference_in_data:
                        self.errors.append(
                            'In %s case returned value does not match expected in %s' % (key, repr(difference_in_data)))
                    wallet.close_send_transaction_view_button.click()
                wallet.home_button.click()
            if 'dapp' in key:
                home.open_in_status_button.click()
                if not (chat.allow_button.is_element_displayed() or chat.element_by_text(
                        "Can't find web3 library").is_element_displayed()):
                    self.errors.append('No allow button is shown in case of navigating to Status dapp!')
                chat.dapp_tab_button.click()
                chat.home_button.click()
            if 'public' in key:
                if not chat.chat_message_input.is_element_displayed():
                    self.errors.append('No message input is shown in case of navigating to public chat via deep link!')
                if not chat.element_by_text_part(url_data[key]['chat_name']).is_element_displayed():
                    self.errors.append('Chat name is not shown in case of navigating to public chat via deep link!')
            chat.get_back_to_home_view()

        self.errors.verify_no_errors()

    # TODO: merge with other 1-driver medium e2e
    @marks.testrail_id(6282)
    def test_scan_qr_eip_681_links_via_wallet(self):
        sign_in = SignInView(self.driver)
        sign_in.recover_access(transaction_senders['C']['passphrase'])
        wallet = sign_in.wallet_button.click()
        wallet.wait_balance_is_changed()
        send_transaction_view = SendTransactionView(self.driver)

        sign_in.just_fyi("Setting up wallet")
        wallet.accounts_status_account.click_until_presence_of_element(wallet.send_transaction_button)
        send_transaction = wallet.send_transaction_button.click()
        send_transaction.set_recipient_address('0x%s' % basic_user['address'])
        send_transaction.amount_edit_box.set_value("0")
        send_transaction.confirm()
        send_transaction.sign_transaction_button.click()
        wallet.set_up_wallet_when_sending_tx()
        wallet.cancel_button.click()
        wallet.close_button.click()

        url_data = {
            'ens_for_receiver': {
                'url': 'ethereum:0xc55cf4b03948d7ebc8b9e8bad92643703811d162@3/transfer?address=nastya.stateofus.eth&uint256=1e-1',
                'data': {
                    'asset': 'STT',
                    'amount': '0.1',
                    'address': '0x58d8…F2ff',
                },
            },
            # 'gas_settings': {
            #     'url': 'ethereum:0x3d597789ea16054a084ac84ce87f50df9198f415@3?value=1e16&gasPrice=1000000000&gasLimit=100000',
            #     'data': {
            #         'amount': '0.01',
            #         'asset': 'ETHro',
            #         'address': '0x3D59…F415',
            #         'gas_limit': '100000',
            #         'gas_price': '1',
            #     },
            # },
            'payment_link': {
                'url': 'ethereum:pay-0xc55cf4b03948d7ebc8b9e8bad92643703811d162@3/transfer?address=0x3d597789ea16054a084ac84ce87f50df9198f415&uint256=1e1',
                'data': {
                    'amount': '10',
                    'asset': 'STT',
                    'address': '0x3D59…F415',
                },
            },
            'validation_amount_too_presize': {
                'url': 'ethereum:0xc55cf4b03948d7ebc8b9e8bad92643703811d162@3/transfer?address=0x101848D5C5bBca18E6b4431eEdF6B95E9ADF82FA&uint256=1e-19',
                'data': {
                    'amount': '1e-19',
                    'asset': 'STT',
                    'address': '0x1018…82FA',

                },
                'send_transaction_validation_error': 'Amount is too precise',
            },
            'validation_amount_too_big': {
                'url': 'ethereum:0x101848D5C5bBca18E6b4431eEdF6B95E9ADF82FA@3?value=1e25',
                'data': {
                    'amount': '10000000',
                    'asset': 'ETHro',
                    'address': '0x1018…82FA',

                },
                'send_transaction_validation_error': 'Insufficient funds',
            },
            'validation_wrong_chain_id': {
                'url': 'ethereum:0x101848D5C5bBca18E6b4431eEdF6B95E9ADF82FA?value=1e17',
                'error': 'Network does not match',
                'data': {
                    'amount': '0.1',
                    'asset': 'ETHro',
                    'address': '0x1018…82FA',
                },
            },
            'validation_wrong_address': {
                'url': 'ethereum:0x744d70fdbe2ba4cf95131626614a1763df805b9e@3/transfer?address=blablabla&uint256=1e10',
                'error': 'Invalid address',
            },
        }

        for key in url_data:
            wallet.just_fyi('Checking %s case' % key)
            wallet.scan_qr_button.click()
            if wallet.allow_button.is_element_displayed():
                wallet.allow_button.click()
            wallet.enter_qr_edit_box.scan_qr(url_data[key]['url'])
            if url_data[key].get('error'):
                if not wallet.element_by_text_part(url_data[key]['error']).is_element_displayed():
                    self.errors.append('Expected error %s is not shown' % url_data[key]['error'])
                wallet.ok_button.click()
            if url_data[key].get('data'):
                actual_data = send_transaction_view.get_values_from_send_transaction_bottom_sheet()
                difference_in_data = url_data[key]['data'].items() - actual_data.items()
                if difference_in_data:
                    self.errors.append(
                        'In %s case returned value does not match expected in %s' % (key, repr(difference_in_data)))
                if url_data[key].get('send_transaction_validation_error'):
                    error = url_data[key]['send_transaction_validation_error']
                    if not wallet.element_by_text_part(error).is_element_displayed():
                        self.errors.append(
                            'Expected error %s is not shown' % error)
                if wallet.close_send_transaction_view_button.is_element_displayed():
                    wallet.close_send_transaction_view_button.wait_and_click()
                else:
                    wallet.cancel_button.wait_and_click()

        self.errors.verify_no_errors()

    @marks.testrail_id(6311)
    # TODO: can be added to any group where kk multiaccount with money is restored as additional check
    def test_keycard_same_seed_added_inside_multiaccount(self):
        sign_in = SignInView(self.driver)
        recipient = "0x" + transaction_senders['ETH_1']['address']
        user = transaction_senders['ETH_STT_4']

        sign_in.just_fyi('Restore keycard multiaccount and logout')
        sign_in.recover_access(passphrase=user['passphrase'], keycard=True)
        profile_view = sign_in.profile_button.click()
        profile_view.logout()

        sign_in.just_fyi('Create new multiaccount')
        sign_in.close_button.click()
        sign_in.your_keys_more_icon.click()
        sign_in.generate_new_key_button.click()
        sign_in.next_button.click()
        sign_in.next_button.click()
        sign_in.create_password_input.set_value(common_password)
        sign_in.next_button.click()
        sign_in.confirm_your_password_input.set_value(common_password)
        sign_in.next_button.click()
        sign_in.maybe_later_button.click_until_presence_of_element(sign_in.lets_go_button)
        sign_in.lets_go_button.click()

        sign_in.just_fyi('Add to wallet seed phrase for restored multiaccount')
        wallet = sign_in.wallet_button.click()
        wallet.add_account_button.click()
        wallet.enter_a_seed_phrase_button.click()
        wallet.enter_your_password_input.send_keys(common_password)
        account_name = 'subacc'
        wallet.account_name_input.send_keys(account_name)
        wallet.enter_seed_phrase_input.set_value(user['passphrase'])
        wallet.add_account_generate_account_button.click()
        wallet.get_account_by_name(account_name).click()

        sign_in.just_fyi('Send transaction from added account and log out')
        transaction_amount_added = wallet.get_unique_amount()
        wallet.send_transaction(from_main_wallet=False, amount=transaction_amount_added, recipient=recipient,
                                sign_transaction=True)
        wallet.profile_button.click()
        profile_view.logout()

        sign_in.just_fyi('Login to keycard account and send another transaction')
        sign_in.back_button.click()
        sign_in.sign_in(position=2, keycard=True)
        sign_in.wallet_button.click()
        wallet.wait_balance_is_changed('ETH')
        transaction_amount_keycard = wallet.get_unique_amount()
        wallet.send_transaction(amount=transaction_amount_keycard, recipient=recipient, keycard=True,
                                sign_transaction=True)

        for amount in [transaction_amount_keycard, transaction_amount_added]:
            sign_in.just_fyi("Checking '%s' tx" % amount)
            self.network_api.find_transaction_by_unique_amount(user['address'], amount)

        self.errors.verify_no_errors()

    @marks.testrail_id(6292)
    # TODO: better to recover user already eith
    def test_keycard_send_funds_between_accounts_set_max_in_multiaccount_instance(self):
        sign_in_view = SignInView(self.driver).create_user(keycard=True)
        wallet = sign_in_view.wallet_button.click()
        status_account_address = wallet.get_wallet_address()[2:]
        self.network_api.get_donate(status_account_address, external_faucet=True)
        wallet.wait_balance_is_changed()
        account_name = 'subaccount'
        wallet.add_account(account_name, keycard=True)
        wallet.get_account_by_name(account_name).click()
        wallet.get_account_options_by_name(account_name).click()
        wallet.account_settings_button.click()
        wallet.swipe_up()

        wallet.just_fyi("Checking that delete account and importing account are not available on keycard")
        if wallet.delete_account_button.is_element_displayed(10):
            self.errors.append('Delete account option is shown on added account "On Status Tree"!')
        wallet.wallet_button.double_click()
        wallet.add_account_button.click()
        if wallet.enter_a_seed_phrase_button.is_element_displayed():
            self.errors.append('Importing account option is available on keycard!')
        wallet.click_system_back_button()

        wallet.just_fyi("Send transaction to new account")
        transaction_amount = '0.006'
        initial_balance = self.network_api.get_balance(status_account_address)
        wallet.send_transaction(account_name=account_name, amount=transaction_amount, keycard=True)
        self.network_api.wait_for_confirmation_of_transaction(status_account_address, transaction_amount)
        self.network_api.verify_balance_is_updated(str(initial_balance), status_account_address)

        wallet.just_fyi("Verifying previously sent transaction in new account")
        wallet.get_account_by_name(account_name).click()
        wallet.send_transaction_button.click()
        wallet.close_send_transaction_view_button.click()
        balance_after_receiving_tx = float(wallet.get_asset_amount_by_name('ETH'))
        expected_balance = self.network_api.get_rounded_balance(balance_after_receiving_tx, transaction_amount)
        if balance_after_receiving_tx != expected_balance:
            self.driver.fail('New account balance %s does not match expected %s after receiving a transaction' % (
                balance_after_receiving_tx, transaction_amount))

        wallet.just_fyi("Sending eth from new account to main account")
        updated_balance = self.network_api.get_balance(status_account_address)
        transaction_amount_1 = round(float(transaction_amount) * 0.2, 11)
        wallet.wait_balance_is_changed()
        wallet.get_account_by_name(account_name).click()
        send_transaction = wallet.send_transaction(from_main_wallet=False, account_name=wallet.status_account_name,
                                                   amount=transaction_amount_1, keycard=True)
        wallet.close_button.click()
        sub_account_address = wallet.get_wallet_address(account_name)[2:]
        self.network_api.wait_for_confirmation_of_transaction(sub_account_address, transaction_amount_1)
        wallet.find_transaction_in_history(amount=format(float(transaction_amount_1), '.11f').rstrip('0'))

        wallet.just_fyi("Check transactions on subaccount")
        self.network_api.verify_balance_is_updated(updated_balance, status_account_address)

        wallet.just_fyi("Verify total ETH on main wallet view")
        self.network_api.wait_for_confirmation_of_transaction(status_account_address, transaction_amount_1)
        self.network_api.verify_balance_is_updated((updated_balance + transaction_amount_1), status_account_address)
        wallet.close_button.click()
        balance_of_sub_account = float(self.network_api.get_balance(sub_account_address)) / 1000000000000000000
        balance_of_status_account = float(self.network_api.get_balance(status_account_address)) / 1000000000000000000
        wallet.scan_tokens()
        total_eth_from_two_accounts = float(wallet.get_asset_amount_by_name('ETH'))
        expected_balance = self.network_api.get_rounded_balance(total_eth_from_two_accounts,
                                                                (balance_of_status_account + balance_of_sub_account))

        if total_eth_from_two_accounts != expected_balance:
            self.driver.fail('Total wallet balance %s != of Status account (%s) + SubAccount (%s)' % (
                total_eth_from_two_accounts, balance_of_status_account, balance_of_sub_account))

        wallet.just_fyi("Check that can set max and send transaction with max amount from subaccount")
        wallet.get_account_by_name(account_name).click()
        wallet.send_transaction_button.click()
        send_transaction.set_max_button.click()
        set_amount = float(send_transaction.amount_edit_box.text)
        if set_amount == 0.0 or set_amount >= balance_of_sub_account:
            self.driver.fail('Value after setting up max amount is set to %s' % str(set_amount))
        send_transaction.confirm()
        send_transaction.chose_recipient_button.click()
        send_transaction.accounts_button.click()
        send_transaction.element_by_text(wallet.status_account_name).click()
        send_transaction.sign_transaction_button.click()
        send_transaction.sign_transaction(keycard=True)
        wallet.element_by_text('Assets').click()
        wallet.wait_balance_is_equal_expected_amount(asset='ETH', expected_balance=0, main_screen=False)

    @marks.testrail_id(5742)
    # TODO: can be separate group of medium onboarding e2e
    def test_keycard_onboarding_interruption_creating_flow(self):
        sign_in = SignInView(self.driver)

        sign_in.just_fyi('Cancel on PIN code setup stage')
        sign_in.accept_tos_checkbox.enable()
        sign_in.get_started_button.click()
        sign_in.generate_key_button.click()
        username = sign_in.first_username_on_choose_chat_name.text
        sign_in.next_button.click()
        keycard_flow = sign_in.keycard_storage_button.click()
        keycard_flow.next_button.click()
        keycard_flow.begin_setup_button.click()
        keycard_flow.connect_card_button.wait_and_click()
        keycard_flow.enter_another_pin()
        keycard_flow.cancel_button.click()

        sign_in.just_fyi('Cancel from Confirm seed phrase: initialized + 1 pairing slot is used')
        keycard_flow.begin_setup_button.click()
        keycard_flow.enter_default_pin()
        keycard_flow.enter_default_pin()
        seed_phrase = keycard_flow.get_seed_phrase()
        keycard_flow.confirm_button.click()
        keycard_flow.yes_button.click()
        keycard_flow.cancel_button.click()
        if not keycard_flow.element_by_text_part('Back up seed phrase').is_element_displayed():
            self.driver.fail('On canceling setup from Confirm seed phrase was not redirected to expected screen')

        sign_in.just_fyi('Cancel from Back Up seed phrase: initialized + 1 pairing slot is used')
        keycard_flow.cancel_button.click()
        keycard_flow.begin_setup_button.click()
        keycard_flow.element_by_translation_id("back-up-seed-phrase").wait_for_element(10)
        new_seed_phrase = keycard_flow.get_seed_phrase()
        if new_seed_phrase != seed_phrase:
            self.errors.append('Another seed phrase is shown after cancelling setup during Back up seed phrase')
        keycard_flow.backup_seed_phrase()
        keycard_flow.enter_default_pin()
        for element in sign_in.maybe_later_button, sign_in.lets_go_button:
            element.wait_for_visibility_of_element(30)
            element.click()
        sign_in.profile_button.wait_for_visibility_of_element(30)

        sign_in.just_fyi('Check username and relogin')
        profile = sign_in.get_profile_view()
        public_key, real_username = profile.get_public_key_and_username(return_username=True)
        if real_username != username:
            self.errors.append('Username was changed after interruption of creating account')
        profile.logout()
        home = sign_in.sign_in(keycard=True)
        if not home.wallet_button.is_element_displayed(10):
            self.errors.append("Failed to login to Keycard account")
        self.errors.verify_no_errors()

    @marks.testrail_id(6246)
    # TODO: can be separate group of medium onboarding e2e
    def test_keycard_onboarding_interruption_access_key_flow(self):
        sign_in = SignInView(self.driver)
        sign_in.accept_tos_checkbox.enable()
        sign_in.get_started_button.click()

        sign_in.access_key_button.click()
        sign_in.enter_seed_phrase_button.click()
        sign_in.seedphrase_input.click()
        sign_in.seedphrase_input.set_value(basic_user['passphrase'])
        sign_in.next_button.click()
        sign_in.reencrypt_your_key_button.click()
        keycard_flow = sign_in.keycard_storage_button.click()

        sign_in.just_fyi('Cancel on PIN code setup stage')
        keycard_flow.next_button.click()
        keycard_flow.begin_setup_button.click()
        keycard_flow.connect_card_button.wait_and_click()
        keycard_flow.enter_another_pin()
        keycard_flow.cancel_button.click()

        sign_in.just_fyi('Finish setup and relogin')
        keycard_flow.begin_setup_button.click()
        keycard_flow.enter_default_pin()
        keycard_flow.enter_default_pin()
        for element in sign_in.maybe_later_button, sign_in.lets_go_button:
            element.wait_for_visibility_of_element(30)
            element.click()
        sign_in.profile_button.wait_for_visibility_of_element(30)
        public_key, default_username = sign_in.get_public_key_and_username(return_username=True)
        profile_view = sign_in.get_profile_view()
        if public_key != basic_user['public_key']:
            self.errors.append('Public key %s does not match expected' % public_key)
        if default_username != basic_user['username']:
            self.errors.append('Default username %s does not match expected' % default_username)
        profile_view.logout()
        home = sign_in.sign_in(keycard=True)
        if not home.wallet_button.is_element_displayed(10):
            self.errors.append("Failed to login to Keycard account")
        self.errors.verify_no_errors()

    @marks.testrail_id(6243)
    # TODO: add to keycard medium group e2e
    def test_keycard_can_recover_keycard_account_offline_and_add_watch_only_acc(self):
        sign_in = SignInView(self.driver)
        sign_in.toggle_airplane_mode()

        sign_in.just_fyi('Recover multiaccount offline')
        sign_in.accept_tos_checkbox.enable()
        sign_in.get_started_button.click_until_presence_of_element(sign_in.access_key_button)
        sign_in.access_key_button.click()
        sign_in.recover_with_keycard_button.click()
        keycard_view = sign_in.begin_recovery_button.click()
        keycard_view.connect_pairing_card_button.click()
        keycard_view.pair_code_input.set_value(pair_code)
        keycard_view.confirm()
        keycard_view.enter_default_pin()
        sign_in.maybe_later_button.click_until_presence_of_element(sign_in.lets_go_button)
        sign_in.lets_go_button.click_until_absense_of_element(sign_in.lets_go_button)
        sign_in.home_button.wait_for_visibility_of_element(30)
        wallet_view = sign_in.wallet_button.click()

        sign_in.just_fyi('Relogin offline')
        self.driver.close_app()
        self.driver.launch_app()
        sign_in.sign_in(keycard=True)
        if not sign_in.home_button.is_element_displayed(10):
            self.driver.fail('Keycard user is not logged in')

        sign_in.just_fyi('Turn off airplane mode and turn on cellular network')
        sign_in.toggle_airplane_mode()
        sign_in.toggle_mobile_data()
        sign_in.element_by_text_part('Stop syncing').wait_and_click(60)
        sign_in.wallet_button.click()
        if not wallet_view.element_by_text_part('LXS').is_element_displayed():
            self.errors.append('Token balance is not fetched while on cellular network!')

        wallet_view.just_fyi('Add watch-only account when on cellular network')
        wallet_view.add_account_button.click()
        wallet_view.add_watch_only_address_button.click()
        wallet_view.enter_address_input.send_keys(basic_user['address'])
        account_name = 'watch-only'
        wallet_view.account_name_input.send_keys(account_name)
        wallet_view.add_account_generate_account_button.click()
        account_button = wallet_view.get_account_by_name(account_name)
        if not account_button.is_element_displayed():
            self.driver.fail('Account was not added')

        wallet_view.just_fyi('Check that balance is changed after go back to WI-FI')
        sign_in.toggle_mobile_data()
        for asset in ('ADI', 'STT'):
            wallet_view.asset_by_name(asset).scroll_to_element()
            wallet_view.wait_balance_is_changed(asset, wait_time=60)

        wallet_view.just_fyi('Delete watch-only account')
        wallet_view.get_account_by_name(account_name).click()
        wallet_view.get_account_options_by_name(account_name).click()
        wallet_view.account_settings_button.click()
        wallet_view.delete_account_button.click()
        wallet_view.yes_button.click()
        if wallet_view.get_account_by_name(account_name).is_element_displayed(20):
            self.errors.append('Account was not deleted')

        self.errors.verify_no_errors()

    @marks.testrail_id(695841)
    # TODO: add to keycard medium group e2e
    def test_keycard_settings_pin_puk_pairing(self):
        sign_in = SignInView(self.driver)
        seed = basic_user['passphrase']
        home = sign_in.recover_access(passphrase=seed, keycard=True)
        profile = home.profile_button.click()

        home.just_fyi("Checking changing PIN")
        profile.keycard_button.scroll_and_click()
        keycard = profile.change_pin_button.click()
        keycard.enter_another_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_default_pin()
        if not keycard.element_by_translation_id("new-pin-description").is_element_displayed():
            self.driver.fail("Screen for setting new pin is not shown!")
        [keycard.enter_another_pin() for _ in range(2)]
        if not keycard.element_by_translation_id("pin-changed").is_element_displayed(30):
            self.driver.fail("Popup about successful setting new PIN is not shown!")
        keycard.ok_button.click()

        home.just_fyi("Checking changing PUK with new PIN")
        profile.change_puk_button.click()
        keycard.enter_another_pin()
        if not keycard.element_by_translation_id("new-puk-description").is_element_displayed():
            self.driver.fail("Screen for setting new puk is not shown!")
        [keycard.one_button.click() for _ in range(12)]
        if not keycard.element_by_translation_id("repeat-puk").is_element_displayed():
            self.driver.fail("Confirmation screen for setting new puk is not shown!")
        [keycard.one_button.click() for _ in range(12)]
        if not keycard.element_by_translation_id("puk-changed").is_element_displayed(30):
            self.driver.fail("Popup about successful setting new PUK is not shown!")
        keycard.ok_button.click()

        home.just_fyi("Checking setting pairing with new PIN")
        profile.change_pairing_code_button.click()
        keycard.enter_another_pin()
        sign_in.create_password_input.wait_for_element()
        sign_in.create_password_input.set_value(common_password)
        sign_in.confirm_your_password_input.set_value(common_password + "1")
        if not keycard.element_by_translation_id("pairing-code_error1").is_element_displayed():
            self.errors.append("No error is shown when pairing codes don't match")
        sign_in.confirm_your_password_input.delete_last_symbols(1)
        sign_in.element_by_translation_id("change-pairing").click()
        if not keycard.element_by_translation_id("pairing-changed").is_element_displayed(30):
            self.driver.fail("Popup about successful setting new pairing is not shown!")
        keycard.ok_button.click()

        home.just_fyi("Checking backing up keycard")
        profile.create_keycard_backup_button.scroll_and_click()
        sign_in.seedphrase_input.set_value(seed)
        sign_in.next_button.click()
        keycard.return_card_to_factory_settings_checkbox.enable()
        keycard.begin_setup_button.click()
        keycard.yes_button.wait_and_click()
        [keycard.enter_another_pin() for _ in range(2)]
        keycard.element_by_translation_id("keycard-backup-success-title").wait_for_element(30)
        keycard.ok_button.click()

        self.errors.verify_no_errors()

    @marks.testrail_id(695851)
    # TODO: add to keycard medium group e2e
    def test_keycard_frozen_card_flows(self):
        sign_in = SignInView(self.driver)
        seed = basic_user['passphrase']
        home = sign_in.recover_access(passphrase=seed, keycard=True)
        profile = home.profile_button.click()
        profile.keycard_button.scroll_and_click()

        home.just_fyi('Set new PUK')
        keycard = profile.change_puk_button.click()
        keycard.enter_default_pin()
        [keycard.enter_default_puk() for _ in range(2)]
        keycard.ok_button.click()

        home.just_fyi("Checking reset with PUK when logged in")
        keycard = profile.change_pin_button.click()
        keycard.enter_another_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_another_pin()
        keycard.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_another_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed(30):
            self.driver.fail("No popup about frozen keycard is shown!")
        home.element_by_translation_id("keycard-is-frozen-reset").click()
        keycard.enter_another_pin()
        home.element_by_text_part('2/2').wait_for_element(20)
        keycard.enter_another_pin()
        home.element_by_translation_id("enter-puk-code").click()
        keycard.enter_default_puk()
        home.element_by_translation_id("keycard-access-reset").wait_for_element(20)
        home.profile_button.double_click()
        profile.logout()

        home.just_fyi("Checking reset with PUK when logged out")
        keycard.enter_default_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_default_pin()
        keycard.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_default_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed():
            self.driver.fail("No popup about frozen keycard is shown!")
        home.element_by_translation_id("keycard-is-frozen-reset").click()
        keycard.enter_another_pin()
        home.element_by_text_part('2/2').wait_for_element(20)
        keycard.enter_another_pin()
        home.element_by_translation_id("enter-puk-code").click()
        keycard.enter_default_puk()
        home.element_by_translation_id("keycard-access-reset").wait_for_element(20)
        home.element_by_translation_id("open").click()

        home.just_fyi("Checking reset with seed when logged in")
        profile = home.profile_button.click()
        profile.keycard_button.scroll_and_click()
        profile.change_pin_button.click()
        keycard.enter_default_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_default_pin()
        keycard.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_default_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed():
            self.driver.fail("No popup about frozen keycard is shown!")
        home.element_by_translation_id("dismiss").click()
        profile.profile_button.double_click()
        profile.keycard_button.scroll_and_click()
        profile.change_pin_button.click()
        keycard.enter_default_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed(30):
            self.driver.fail("No reset card flow is shown for frozen card")
        home.element_by_translation_id("keycard-is-frozen-factory-reset").click()
        sign_in.seedphrase_input.set_value(transaction_senders['A']['passphrase'])
        sign_in.next_button.click()
        if not home.element_by_translation_id("seed-key-uid-mismatch").is_element_displayed():
            self.driver.fail("No popup about mismatch in seed phrase is shown!")
        home.element_by_translation_id("try-again").click()
        sign_in.seedphrase_input.clear()
        sign_in.seedphrase_input.set_value(seed)
        sign_in.next_button.click()
        keycard.begin_setup_button.click()
        keycard.yes_button.click()
        keycard.enter_default_pin()
        home.element_by_translation_id("intro-wizard-title5").wait_for_element(20)
        keycard.enter_default_pin()
        home.element_by_translation_id("keycard-access-reset").wait_for_element(30)
        home.ok_button.click()
        profile.profile_button.double_click()
        profile.logout()

        home.just_fyi("Checking reset with seed when logged out")
        keycard.enter_another_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_another_pin()
        keycard.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_another_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed():
            self.driver.fail("No popup about frozen keycard is shown!")

        sign_in.element_by_translation_id("keycard-is-frozen-factory-reset").click()
        sign_in.seedphrase_input.set_value(seed)
        sign_in.next_button.click()
        keycard.begin_setup_button.click()
        keycard.yes_button.click()
        keycard.enter_default_pin()
        home.element_by_translation_id("intro-wizard-title5").wait_for_element(20)
        keycard.enter_default_pin()
        home.element_by_translation_id("keycard-access-reset").wait_for_element(30)
        home.ok_button.click()
        keycard.enter_default_pin()
        home.home_button.wait_for_element(30)

    @marks.testrail_id(695852)
    # TODO: add to keycard medium group e2e
    def test_keycard_blocked_card_lost_or_frozen_flows(self):
        sign_in = SignInView(self.driver)
        seed = basic_user['passphrase']
        home = sign_in.recover_access(passphrase=seed, keycard=True)
        profile = home.profile_button.click()
        profile.keycard_button.scroll_and_click()

        home.just_fyi("Checking blocked card screen when entering 3 times invalid PIN + 5 times invalid PUK")
        keycard = profile.change_pin_button.click()
        keycard.enter_another_pin()
        keycard.wait_for_element_starts_with_text('2 attempts left', 30)
        keycard.enter_another_pin()
        keycard.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_another_pin()
        if not home.element_by_translation_id("keycard-is-frozen-title").is_element_displayed():
            self.driver.fail("No popup about frozen keycard is shown!")
        home.element_by_translation_id("keycard-is-frozen-reset").click()
        keycard.enter_another_pin()
        home.element_by_text_part('2/2').wait_for_element(20)
        keycard.enter_another_pin()
        home.element_by_translation_id("enter-puk-code").click()

        for i in range(1, 4):
            keycard.enter_default_puk()
            sign_in.wait_for_element_starts_with_text('%s attempts left' % str(5 - i))
            i += 1
        keycard.enter_default_puk()
        sign_in.element_by_text_part('one attempt').wait_for_element(30)
        keycard.enter_default_puk()
        keycard.element_by_translation_id("keycard-is-blocked-title").wait_for_element(30)
        keycard.close_button.click()
        if not keycard.element_by_translation_id("keycard-blocked").is_element_displayed():
            self.errors.append("In keycard settings there is no info that card is blocked")
        keycard.back_button.click()
        profile.logout()

        home.just_fyi("Check blocked card when user is logged out and use lost or frozen to restore access")
        keycard.enter_another_pin()
        keycard.element_by_translation_id("keycard-is-blocked-title").wait_for_element(30)
        keycard.element_by_translation_id("keycard-recover").click()
        keycard.yes_button.click()
        sign_in.seedphrase_input.set_value(seed)
        sign_in.next_button.click()
        keycard.begin_setup_button.click()
        keycard.yes_button.click()
        keycard.enter_default_pin()
        home.element_by_translation_id("intro-wizard-title5").wait_for_element(20)
        keycard.enter_default_pin()
        home.element_by_translation_id("keycard-access-reset").wait_for_element(30)
        home.ok_button.click()
        keycard.enter_default_pin()
        home.home_button.wait_for_element(30)

        self.errors.verify_no_errors()

    @marks.testrail_id(6310)
    # TODO: add to keycard medium group e2e
    def test_keycard_testdapp_sign_typed_message_deploy_simple_contract_send_tx(self):
        sender = transaction_senders['ETH_6']
        home = SignInView(self.driver).recover_access(sender['passphrase'], keycard=True)
        wallet = home.wallet_button.click()
        status_test_dapp = home.open_status_test_dapp()
        status_test_dapp.wait_for_d_aap_to_load()
        status_test_dapp.transactions_button.click_until_presence_of_element(status_test_dapp.sign_typed_message_button)

        wallet.just_fyi("Checking sign typed message")
        send_transaction = status_test_dapp.sign_typed_message_button.click()
        send_transaction.sign_with_keycard_button.click()
        keycard_view = send_transaction.sign_with_keycard_button.click()
        keycard_view.enter_default_pin()
        if not keycard_view.element_by_text_part('0x6df0ce').is_element_displayed():
            self.errors.append('Typed message was not signed')

        wallet.just_fyi("Checking deploy simple contract")
        send_transaction_view = status_test_dapp.deploy_contract_button.click()
        send_transaction_view.sign_transaction(keycard=True)
        if not status_test_dapp.element_by_text('Contract deployed at: ').is_element_displayed(300):
            self.driver.fail('Contract was not created or tx taking too long')
        for text in ['Call contract get function',
                     'Call contract set function', 'Call function 2 times in a row']:
            status_test_dapp.element_by_text(text).scroll_to_element()
        self.errors.verify_no_errors()

    @marks.testrail_id(6295)
    # TODO: may be merged with 6294 to group and add more tx tests
    def test_keycard_send_tx_eth_to_ens(self):
        sign_in = SignInView(self.driver)
        sender = transaction_senders['ETH_4']
        home = sign_in.recover_access(sender['passphrase'], keycard=True)
        wallet = home.wallet_button.click()
        wallet.home_button.click()

        chat = home.add_contact(ens_user_ropsten['ens'])
        chat.commands_button.click()
        amount = chat.get_unique_amount()

        send_message = chat.send_command.click()
        send_message.amount_edit_box.set_value(amount)
        send_message.confirm()
        send_message.next_button.click()

        from views.send_transaction_view import SendTransactionView
        send_transaction = SendTransactionView(self.driver)
        send_transaction.sign_transaction(keycard=True)
        chat_sender_message = chat.get_outgoing_transaction()
        self.network_api.wait_for_confirmation_of_transaction(sender['address'], amount)
        chat_sender_message.transaction_status.wait_for_element_text(chat_sender_message.confirmed)

    @marks.testrail_id(695890)
    # TODO: may be split into several more atomic e2e and added to group of profile e2e
    def test_profile_use_another_fleets_balance_bsc_xdai_advanced_set_nonce(self):
        user = user_mainnet
        sign_in = SignInView(self.driver)
        home = sign_in.recover_access(user['passphrase'])

        home.just_fyi("Check that can enable all toggles and still login successfully")
        profile = home.profile_button.click()
        profile.advanced_button.click()
        profile.transaction_management_enabled_toggle.click()
        profile.webview_debug_toggle.click()
        profile.waku_bloom_toggle.scroll_and_click()
        sign_in.sign_in()

        home.just_fyi("Check tx management")
        wallet = home.wallet_button.click()
        send_tx = wallet.send_transaction_from_main_screen.click()
        from views.send_transaction_view import SendTransactionView
        send_tx = SendTransactionView(self.driver)
        send_tx.amount_edit_box.set_value('0')
        send_tx.set_recipient_address(transaction_senders['ETH_7']['address'])
        send_tx.next_button.click()
        send_tx.set_up_wallet_when_sending_tx()
        send_tx.advanced_button.click()
        send_tx.nonce_input.set_value('4')
        send_tx.nonce_save_button.click()
        error_text = send_tx.sign_transaction(error=True)
        if error_text != 'nonce too low':
            self.errors.append("%s is not expected error when signing tx with custom nonce" % error_text)

        home.just_fyi("Check balance on mainnet")
        profile = home.profile_button.click()
        profile.switch_network()
        wallet = home.wallet_button.click()
        wallet.scan_tokens()
        [wallet.wait_balance_is_equal_expected_amount(asset, value) for asset, value in user['mainnet'].items()]

        home.just_fyi("Check balance on xDai and default network fee")
        profile = home.profile_button.click()
        profile.switch_network('xDai Chain')
        home.wallet_button.click()
        wallet.element_by_text(user['xdai']).wait_for_element(30)

        home.just_fyi("Check balance on BSC and default network fee")
        profile = home.profile_button.click()
        profile.switch_network('BSC Network')
        home.wallet_button.click()
        wallet.element_by_text(user['bsc']).wait_for_element(30)

        self.errors.verify_no_errors()

    @marks.testrail_id(6219)
    # TODO: can bought ens to user from 695890 and use the same user
    def test_profile_set_primary_ens_custom_domain(self):
        home = SignInView(self.driver).recover_access(ens_user['passphrase'])
        ens_second, ens_main = ens_user['ens_another'], ens_user['ens']

        home.just_fyi('add 2 ENS names in Profile')
        profile = home.profile_button.click()
        dapp = profile.connect_existing_ens(ens_main)
        profile.element_by_translation_id("ens-add-username").wait_and_click()
        profile.element_by_translation_id("ens-want-custom-domain").wait_and_click()
        dapp.ens_name_input.set_value(ens_second)
        dapp.check_ens_name.click_until_presence_of_element(dapp.element_by_translation_id("ens-got-it"))
        dapp.element_by_translation_id("ens-got-it").wait_and_click()

        home.just_fyi('check that by default %s ENS is set' % ens_main)
        dapp.element_by_translation_id("ens-primary-username").click()
        message_to_check = 'Your messages are displayed to others with'
        if not dapp.element_by_text('%s\n@%s' % (message_to_check, ens_main)).is_element_displayed():
            self.errors.append('%s ENS username is not set as primary by default' % ens_main)

        home.just_fyi('check view in chat settings ENS from other domain: %s after set new primary ENS' % ens_second)
        dapp.set_primary_ens_username(ens_second).click()
        if profile.username_in_ens_chat_settings_text.text != '@' + ens_second:
            self.errors.append('ENS username %s is not shown in ENS username Chat Settings after enabling' % ens_second)
        self.errors.verify_no_errors()

    @marks.testrail_id(5453)
    # TODO: may be split into several more atomic e2e and added to group of profile e2e
    def test_profile_privacy_policy_terms_of_use_node_version_need_help(self):
        signin = SignInView(self.driver)
        no_link_found_error_msg = 'Could not find privacy policy link at'
        no_link_open_error_msg = 'Could not open our privacy policy from'
        no_link_tos_error_msg = 'Could not open Terms of Use from'

        signin.just_fyi("Checking privacy policy and TOS links")
        if not signin.privacy_policy_link.is_element_present():
            self.errors.append('%s Sign in view!' % no_link_found_error_msg)
        if not signin.terms_of_use_link.is_element_displayed():
            self.driver.fail("No Terms of Use link on Sign in view!")

        home = signin.create_user()
        profile = home.profile_button.click()
        profile.about_button.click()
        profile.privacy_policy_button.click()
        from views.web_views.base_web_view import BaseWebView
        web_page = BaseWebView(self.driver)
        if not web_page.policy_summary.is_element_displayed():
            self.errors.append('%s Profile about view!' % no_link_open_error_msg)
        web_page.click_system_back_button()

        profile.terms_of_use_button.click()
        web_page.wait_for_d_aap_to_load()
        web_page.swipe_by_custom_coordinates(0.5, 0.8, 0.5, 0.4)
        if not web_page.terms_of_use_summary.is_element_displayed(30):
            self.errors.append('%s Profile about view!' % no_link_tos_error_msg)
        web_page.click_system_back_button()

        signin.just_fyi("Checking that version match expected format and can be copied")
        app_version = profile.app_version_text.text
        node_version = profile.node_version_text.text
        if not re.search(r'\d[.]\d{1,2}[.]\d{1,2}\s[(]\d*[)]', app_version):
            self.errors.append("App version %s didn't match expected format" % app_version)
        if not re.search(r'StatusIM/v.*/android-\d{3}/go\d[.]\d+', node_version):
            self.errors.append("Node version %s didn't match expected format" % node_version)
        profile.app_version_text.click()
        profile.back_button.click()
        profile.home_button.click()
        chat = home.join_public_chat(home.get_random_chat_name())
        message_input = chat.chat_message_input
        message_input.paste_text_from_clipboard()
        if message_input.text != app_version:
            self.errors.append('Version number was not copied to clipboard')

        signin.just_fyi("Checking Need help section")
        home.profile_button.double_click()
        profile.help_button.click()
        web_page = profile.faq_button.click()
        web_page.open_in_webview()
        web_page.wait_for_d_aap_to_load()
        if not profile.element_by_text_part("F.A.Q").is_element_displayed(30):
            self.errors.append("FAQ is not shown")
        profile.click_system_back_button()
        profile.submit_bug_button.click()

        signin.just_fyi("Checking bug submitting form")
        profile.bug_description_edit_box.set_value('1234')
        profile.bug_submit_button.click()
        if not profile.element_by_translation_id("bug-report-too-short-description").is_element_displayed():
            self.errors.append("Can submit big with too short description!")
        profile.bug_description_edit_box.clear()
        [field.set_value("Something wrong happened!!") for field in
         (profile.bug_description_edit_box, profile.bug_steps_edit_box)]
        profile.bug_submit_button.click()
        if not profile.element_by_text_part("Welcome to Gmail").is_element_displayed(30):
            self.errors.append("Mail client is not opened when submitting bug")
        profile.click_system_back_button(2)

        signin.just_fyi("Checking request feature")
        profile.request_a_feature_button.click()
        if not profile.element_by_text("#support").is_element_displayed(30):
            self.errors.append("Support channel is not suggested for requesting a feature")
        self.errors.verify_no_errors()

    @marks.testrail_id(5766)
    @marks.flaky
    # TODO: recheck that it is not part of 5436 (suspect duplicate)
    def test_use_pinned_history_node(self):
        home = SignInView(self.driver).create_user()
        profile = home.profile_button.click()

        profile.just_fyi('pin history node')
        profile.sync_settings_button.click()
        node_gc, node_ams, node_hk = [profile.return_mailserver_name(history_node_name, used_fleet) for
                                      history_node_name in (mailserver_gc, mailserver_ams, mailserver_hk)]
        h_node = node_ams
        profile.mail_server_button.click()
        profile.mail_server_auto_selection_button.click()
        profile.mail_server_by_name(h_node).click()
        profile.confirm_button.click()
        if profile.element_by_translation_id("mailserver-error-title").is_element_displayed(10):
            h_node = node_hk
            profile.element_by_translation_id("mailserver-pick-another", uppercase=True).click()
            profile.mail_server_by_name(h_node).click()
            profile.confirm_button.click()
            if profile.element_by_translation_id("mailserver-error-title").is_element_displayed(10):
                self.driver.fail("Couldn't connect to any history node")

        profile.just_fyi('check that history node is pinned')
        profile.close_button.click()
        if not profile.element_by_text(h_node).is_element_displayed():
            self.errors.append('"%s" history node is not pinned' % h_node)
        profile.home_button.click()

        profile.just_fyi('Relogin and check that settings are preserved')
        home.relogin()
        home.profile_button.click()
        profile.sync_settings_button.click()
        if not profile.element_by_text(h_node).is_element_displayed():
            self.errors.append('"%s" history node is not pinned' % h_node)

        self.errors.verify_no_errors()

    @marks.testrail_id(6318)
    # TODO: can be added as last e2e in profile group
    def test_can_delete_several_multiaccounts(self):
        sign_in = SignInView(self.driver)
        sign_in.create_user()
        delete_alert_warning = sign_in.get_translation_by_key("delete-profile-warning")
        profile = sign_in.profile_button.click()
        profile.logout()
        if sign_in.ok_button.is_element_displayed():
            sign_in.ok_button.click()
        sign_in.back_button.click()
        sign_in.your_keys_more_icon.click()
        sign_in.generate_new_key_button.click()
        sign_in.next_button.click()
        sign_in.next_button.click()
        sign_in.create_password_input.set_value(common_password)
        sign_in.next_button.click()
        sign_in.confirm_your_password_input.set_value(common_password)
        sign_in.next_button.click()
        sign_in.maybe_later_button.click_until_presence_of_element(sign_in.lets_go_button)
        sign_in.lets_go_button.click()

        sign_in.just_fyi('Delete 2nd multiaccount')
        public_key, username = sign_in.get_public_key_and_username(return_username=True)
        profile.privacy_and_security_button.click()
        profile.delete_my_profile_button.scroll_and_click()
        for text in (username, delete_alert_warning):
            if not profile.element_by_text(text).is_element_displayed():
                self.errors.append('Required %s is not shown when deleting multiaccount' % text)
        profile.delete_profile_button.click()
        if profile.element_by_translation_id("profile-deleted-title").is_element_displayed():
            self.driver.fail('Profile is deleted without confirmation with password')
        profile.delete_my_profile_password_input.set_value(common_password)
        profile.delete_profile_button.click_until_presence_of_element(
            profile.element_by_translation_id("profile-deleted-title"))
        profile.ok_button.click()

        sign_in.just_fyi('Delete last multiaccount')
        sign_in.sign_in()
        sign_in.profile_button.click()
        profile.privacy_and_security_button.click()
        profile.delete_my_profile_button.scroll_and_click()
        profile.delete_my_profile_password_input.set_value(common_password)
        profile.delete_profile_button.click()
        profile.ok_button.click()
        if not sign_in.get_started_button.is_element_displayed(20):
            self.errors.append('No redirected to carousel view after deleting last multiaccount')
        self.errors.verify_no_errors()

    @marks.testrail_id(6225)
    # TODO: can be added as last e2e in wallet group (to group with several accounts as prerequiste)
    def test_wallet_send_tx_between_accounts_in_multiaccount_instance(self):
        sign_in = SignInView(self.driver)
        sign_in.create_user()
        wallet = sign_in.wallet_button.click()
        status_account_address = wallet.get_wallet_address()[2:]
        self.network_api.get_donate(status_account_address, external_faucet=True)
        wallet.wait_balance_is_changed()

        account_name = 'subaccount'
        wallet.add_account(account_name)

        wallet.just_fyi("Send transaction to new account")
        initial_balance = self.network_api.get_balance(status_account_address)

        transaction_amount = '0.003%s' % str(random.randint(10000, 99999)) + '1'
        wallet.send_transaction(account_name=account_name, amount=transaction_amount)
        self.network_api.wait_for_confirmation_of_transaction(status_account_address, transaction_amount)
        self.network_api.verify_balance_is_updated(str(initial_balance), status_account_address)

        wallet.just_fyi("Verifying previously sent transaction in new account")
        wallet.get_account_by_name(account_name).click()
        wallet.send_transaction_button.click()
        wallet.close_send_transaction_view_button.click()
        balance_after_receiving_tx = float(wallet.get_asset_amount_by_name('ETH'))
        expected_balance = self.network_api.get_rounded_balance(balance_after_receiving_tx, transaction_amount)
        if balance_after_receiving_tx != expected_balance:
            self.driver.fail('New account balance %s does not match expected %s after receiving a transaction' % (
                balance_after_receiving_tx, transaction_amount))

        wallet.just_fyi("Sending eth from new account to main account")
        updated_balance = self.network_api.get_balance(status_account_address)
        transaction_amount_1 = round(float(transaction_amount) * 0.2, 12)
        wallet.send_transaction(from_main_wallet=False, account_name=wallet.status_account_name,
                                amount=transaction_amount_1)
        wallet.close_button.click()
        sub_account_address = wallet.get_wallet_address(account_name)[2:]
        self.network_api.wait_for_confirmation_of_transaction(status_account_address, transaction_amount_1)
        self.network_api.verify_balance_is_updated(updated_balance, status_account_address)
        wallet.find_transaction_in_history(amount=transaction_amount)
        wallet.find_transaction_in_history(amount=format(float(transaction_amount_1), '.11f').rstrip('0'))

        wallet.just_fyi("Check transactions on subaccount")
        self.network_api.verify_balance_is_updated(updated_balance, status_account_address)

        wallet.just_fyi("Verify total ETH on main wallet view")
        self.network_api.wait_for_confirmation_of_transaction(status_account_address, transaction_amount_1)
        self.network_api.verify_balance_is_updated((updated_balance + transaction_amount_1), status_account_address)
        wallet.close_button.click()
        balance_of_sub_account = float(self.network_api.get_balance(sub_account_address)) / 1000000000000000000
        balance_of_status_account = float(self.network_api.get_balance(status_account_address)) / 1000000000000000000
        wallet.scan_tokens()
        total_eth_from_two_accounts = float(wallet.get_asset_amount_by_name('ETH'))
        expected_balance = self.network_api.get_rounded_balance(total_eth_from_two_accounts,
                                                                (balance_of_status_account + balance_of_sub_account))

        if total_eth_from_two_accounts != expected_balance:
            self.driver.fail('Total wallet balance %s != of Status account (%s) + SubAccount (%s)' % (
                total_eth_from_two_accounts, balance_of_status_account, balance_of_sub_account))

    @marks.testrail_id(6235)
    # TODO: can be added as last e2e in wallet group (to group with several accounts as prerequiste)
    def test_wallet_can_change_account_settings(self):
        sign_in_view = SignInView(self.driver)
        sign_in_view.create_user()
        wallet_view = sign_in_view.wallet_button.click()
        status_account_address = wallet_view.get_wallet_address()
        wallet_view.get_account_options_by_name().click()

        wallet_view.just_fyi('open Account Settings screen and check that all elements are shown')
        wallet_view.account_settings_button.click()
        for text in 'On Status tree', status_account_address, "m/44'/60'/0'/0/0":
            if not wallet_view.element_by_text(text).is_element_displayed():
                self.errors.append("'%s' text is not shown on Account Settings screen!" % text)

        wallet_view.just_fyi('change account name/color and verified applied changes')
        account_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        wallet_view.account_name_input.clear()
        wallet_view.account_name_input.send_keys(account_name)
        wallet_view.account_color_button.select_color_by_position(1)
        wallet_view.apply_settings_button.click()
        wallet_view.element_by_text('This device').scroll_to_element()
        wallet_view.close_button.click()
        wallet_view.close_button.click()
        account_button = wallet_view.get_account_by_name(account_name)
        if not account_button.is_element_displayed():
            self.driver.fail('Account name was not changed')
        if not account_button.color_matches('multi_account_color.png'):
            self.driver.fail('Account color does not match expected')

        self.errors.verify_no_errors()

    @marks.testrail_id(6232)
    # TODO: can be added as last e2e in wallet group (to group with several accounts as prerequiste)
    # TODO: due to 13011
    def test_testdapp_wallet_permissions_switching_accounts_in_dapp(self):
        home = SignInView(self.driver).create_user()
        wallet = home.wallet_button.click()

        wallet.just_fyi('create new account in multiaccount')
        status_account = home.status_account_name
        account_name = 'Subaccount'
        wallet.add_account(account_name)
        address = wallet.get_wallet_address(account_name)

        home.just_fyi('can see two accounts in DApps')
        dapp = home.dapp_tab_button.click()
        dapp.select_account_button.click()
        for text in 'Select the account', status_account, account_name:
            if not dapp.element_by_text_part(text).is_element_displayed():
                self.driver.fail("No expected element %s is shown in menu" % text)

        home.just_fyi('add permission to Status account')
        dapp.enter_url_editbox.click()
        status_test_dapp = home.open_status_test_dapp()

        home.just_fyi('check that permissions from previous account was removed once you choose another')
        dapp.select_account_button.click()
        dapp.select_account_by_name(account_name).wait_for_element(30)
        dapp.select_account_by_name(account_name).click()
        profile = dapp.profile_button.click()
        profile.privacy_and_security_button.click()
        profile.dapp_permissions_button.click()
        if profile.element_by_text(test_dapp_name).is_element_displayed():
            self.errors.append("Permissions for %s are not removed" % test_dapp_name)

        home.just_fyi('check that can change account')
        profile.dapp_tab_button.click()
        if not status_test_dapp.element_by_text_part(account_name).is_element_displayed():
            self.errors.append("No expected account %s is shown in authorize web3 popup for wallet" % account_name)
        status_test_dapp.allow_button.click()
        dapp.profile_button.click(desired_element_text='DApp permissions')
        profile.element_by_text(test_dapp_name).click()
        for text in 'Chat key', account_name:
            if not dapp.element_by_text_part(text).is_element_displayed():
                self.errors.append("Access is not granted to %s" % text)

        home.just_fyi('check correct account is shown for transaction if sending from DApp')
        profile.dapp_tab_button.click(desired_element_text='Accounts')
        status_test_dapp.assets_button.click()
        send_transaction = status_test_dapp.request_stt_button.click()
        send_transaction.ok_got_it_button.wait_and_click()
        address = send_transaction.get_formatted_recipient_address(address)
        if not send_transaction.element_by_text(address).is_element_displayed():
            self.errors.append("Wallet address %s in not shown in 'From' on Send Transaction screen" % address)

        home.just_fyi('Relogin and check multiaccount loads fine')
        send_transaction.cancel_button.click()
        home.profile_button.click()
        home.relogin()
        home.wallet_button.click()
        if not wallet.element_by_text(account_name).is_element_displayed():
            self.errors.append("Subaccount is gone after relogin in Wallet!")
        home.profile_button.click()
        profile.privacy_and_security_button.click()
        profile.dapp_permissions_button.click()
        profile.element_by_text(test_dapp_name).click()
        if not profile.element_by_text(account_name).is_element_displayed():
            self.errors.append("Subaccount is not selected after relogin in Dapps!")
        self.errors.verify_no_errors()

    @marks.testrail_id(5784)
    # TODO: can be added as last e2e in wallet group (to group with several accounts as prerequiste)
    def test_testdapp_sign_typed_message_deploy_simple_contract_request_pub_key(self):
        user = transaction_senders['ETH_5']
        home = SignInView(self.driver).recover_access(passphrase=user['passphrase'])

        home.just_fyi("Checking requesting public key from dapp")
        status_test_dapp = home.open_status_test_dapp(allow_all=False)
        status_test_dapp.status_api_button.click_until_presence_of_element(status_test_dapp.request_contact_code_button)
        status_test_dapp.request_contact_code_button.click_until_presence_of_element(status_test_dapp.deny_button)
        status_test_dapp.deny_button.click()
        if status_test_dapp.element_by_text(user['public_key']).is_element_displayed():
            self.errors.append('Public key is returned but access was not allowed')
        status_test_dapp.request_contact_code_button.click_until_presence_of_element(status_test_dapp.deny_button)
        status_test_dapp.allow_button.click()
        if not status_test_dapp.element_by_text(user['public_key']).is_element_displayed():
            self.errors.append('Public key is not returned')
        status_test_dapp.get_empty_dapp_tab()
        home.wallet_button.click()

        home.just_fyi("Checking sign typed message")
        home.open_status_test_dapp(allow_all=True)
        status_test_dapp.transactions_button.click_until_presence_of_element(status_test_dapp.sign_typed_message_button)
        send_transaction = status_test_dapp.sign_typed_message_button.click()
        send_transaction.enter_password_input.send_keys(common_password)
        send_transaction.sign_button.click_until_absense_of_element(send_transaction.sign_button)
        if not status_test_dapp.element_by_text_part('0x1673d96e836').is_element_displayed(30):
            self.errors.append("Hash of signed typed message is not shown!")

        home.just_fyi("Checking deploy simple contract")
        send_transaction = status_test_dapp.deploy_contract_button.click()
        send_transaction.sign_transaction()
        if not status_test_dapp.element_by_text('Contract deployed at: ').is_element_displayed(240):
            self.errors.append('Contract was not created')
        for text in ['Call contract get function',
                     'Call contract set function', 'Call function 2 times in a row']:
            status_test_dapp.element_by_text(text).scroll_to_element()
        self.errors.verify_no_errors()

    @marks.testrail_id(5358)
    # TODO: can be added to any group where new multiaccount is created
    def test_wallet_backup_recovery_phrase_warning_from_wallet(self):
        sign_in = SignInView(self.driver)
        sign_in.create_user()
        wallet = sign_in.wallet_button.click()
        if wallet.backup_recovery_phrase_warning_text.is_element_present():
            self.driver.fail("'Back up your seed phrase' warning is shown on Wallet while no funds are present")
        address = wallet.get_wallet_address()
        self.network_api.get_donate(address[2:], external_faucet=True, wait_time=200)
        wallet.close_button.click()
        wallet.wait_balance_is_changed(scan_tokens=True)
        if not wallet.backup_recovery_phrase_warning_text.is_element_present(30):
            self.driver.fail("'Back up your seed phrase' warning is not shown on Wallet with funds")
        profile = wallet.get_profile_view()
        wallet.backup_recovery_phrase_warning_text.click()
        profile.backup_recovery_phrase()

    @marks.testrail_id(5437)
    # TODO: should be in separate group where tx is not sent
    def test_wallet_validation_amount_errors(self):
        sender = wallet_users['C']
        sign_in = SignInView(self.driver)

        errors = {'send_transaction_screen': {
            'too_precise': 'Amount is too precise. Max number of decimals is 7.',
            'insufficient_funds': 'Insufficient funds'
        },
            'sending_screen': {
                'Amount': 'Insufficient funds',
                'Network fee': 'Not enough ETH for gas'
            },
        }
        warning = 'Warning %s is not shown on %s'

        sign_in.recover_access(sender['passphrase'])
        wallet = sign_in.wallet_button.click()
        wallet.wait_balance_is_changed('ADI')
        wallet.accounts_status_account.click()

        screen = 'send transaction screen from wallet'
        sign_in.just_fyi('Checking %s on %s' % (errors['send_transaction_screen']['too_precise'], screen))
        initial_amount_adi = wallet.get_asset_amount_by_name('ADI')
        send_transaction = wallet.send_transaction_button.click()
        adi_button = send_transaction.asset_by_name('ADI')
        send_transaction.select_asset_button.click_until_presence_of_element(
            send_transaction.eth_asset_in_select_asset_bottom_sheet_button)
        adi_button.click()
        send_transaction.amount_edit_box.click()
        amount = '0.000%s' % str(random.randint(100000, 999999)) + '1'
        send_transaction.amount_edit_box.set_value(amount)
        if not send_transaction.element_by_text(
                errors['send_transaction_screen']['too_precise']).is_element_displayed():
            self.errors.append(warning % (errors['send_transaction_screen']['too_precise'], screen))

        sign_in.just_fyi('Checking %s on %s' % (errors['send_transaction_screen']['insufficient_funds'], screen))
        send_transaction.amount_edit_box.clear()
        send_transaction.amount_edit_box.set_value(str(initial_amount_adi) + '1')
        if not send_transaction.element_by_text(
                errors['send_transaction_screen']['insufficient_funds']).is_element_displayed():
            self.errors.append(warning % (errors['send_transaction_screen']['insufficient_funds'], screen))
        wallet.close_send_transaction_view_button.click()
        wallet.close_button.click()

        screen = 'sending screen from wallet'
        sign_in.just_fyi('Checking %s on %s' % (errors['sending_screen']['Network fee'], screen))
        account_name = 'new'
        wallet.add_account(account_name)
        wallet.get_account_by_name(account_name).click()
        wallet.send_transaction_button.click()
        send_transaction.amount_edit_box.set_value('0')
        send_transaction.set_recipient_address(ens_user_ropsten['ens'])
        send_transaction.next_button.click()
        wallet.ok_got_it_button.wait_and_click(30)
        if not send_transaction.validation_error_element.is_element_displayed(10):
            self.errors.append('Validation icon is not shown when testing %s on %s' % (errors['sending_screen']['Network fee'], screen))
        if not wallet.element_by_translation_id("tx-fail-description2").is_element_displayed():
            self.errors.append("No warning about failing tx is shown!")
        send_transaction.cancel_button.click()

        screen = 'sending screen from DApp'
        sign_in.just_fyi('Checking %s on %s' % (errors['sending_screen']['Network fee'], screen))
        home = wallet.home_button.click()
        dapp = sign_in.dapp_tab_button.click()
        dapp.select_account_button.click()
        dapp.select_account_by_name(account_name).wait_for_element(30)
        dapp.select_account_by_name(account_name).click()
        status_test_dapp = home.open_status_test_dapp()
        status_test_dapp.wait_for_d_aap_to_load()
        status_test_dapp.transactions_button.click_until_presence_of_element(
            status_test_dapp.send_two_tx_in_batch_button)
        status_test_dapp.send_two_tx_in_batch_button.click()
        if not send_transaction.validation_error_element.is_element_displayed(10):
            self.errors.append(warning % (errors['sending_screen']['Network fee'], screen))
        self.errors.verify_no_errors()

    @marks.testrail_id(6269)
    # TODO: can be added as last e2e in wallet group (with 5437)
    def test_wallet_search_asset_and_currency(self):
        sign_in = SignInView(self.driver)
        home = sign_in.create_user()
        profile = home.profile_button.click()
        profile.switch_network()
        search_list_assets = {
            'ad': ['AdEx', 'Open Trading Network', 'TrueCAD'],
            'zs': ['ZSC']
        }
        wallet = home.wallet_button.click()

        home.just_fyi('Searching for asset by name and symbol')
        wallet.multiaccount_more_options.click()
        wallet.manage_assets_button.click()
        for keyword in search_list_assets:
            home.search_by_keyword(keyword)
            if keyword == 'ad':
                search_elements = wallet.all_assets_full_names.find_elements()
            else:
                search_elements = wallet.all_assets_symbols.find_elements()
            if not search_elements:
                self.errors.append('No search results after searching by %s keyword' % keyword)
            search_results = [element.text for element in search_elements]
            if search_results != search_list_assets[keyword]:
                self.errors.append("'%s' is shown on the home screen after searching by '%s' keyword" %
                                   (', '.join(search_results), keyword))
            home.cancel_button.click()
        wallet.close_button.click()

        home.just_fyi('Searching for currency')
        search_list_currencies = {
            'aF': ['Afghanistan Afghani (AFN)', 'South Africa Rand (ZAR)'],
            'bolívi': ['Bolivia Bolíviano (BOB)']
        }
        wallet.multiaccount_more_options.click_until_presence_of_element(wallet.set_currency_button)
        wallet.set_currency_button.click()
        for keyword in search_list_currencies:
            home.search_by_keyword(keyword)
            search_elements = wallet.currency_item_text.find_elements()
            if not search_elements:
                self.errors.append('No search results after searching by %s keyword' % keyword)
            search_results = [element.text for element in search_elements]
            if search_results != search_list_currencies[keyword]:
                self.errors.append("'%s' is shown on the home screen after searching by '%s' keyword" %
                                   (', '.join(search_results), keyword))
            home.cancel_button.click()

        self.errors.verify_no_errors()

    @marks.testrail_id(5429)
    # TODO: can be added as last e2e in wallet group (with 5437)
    def test_wallet_set_currency(self):
        home = SignInView(self.driver).create_user()
        user_currency = 'Euro (EUR)'
        wallet = home.wallet_button.click()
        wallet.set_currency(user_currency)
        if not wallet.element_by_text_part('EUR').is_element_displayed(20):
            self.driver.fail('EUR currency is not displayed')

    @marks.testrail_id(5407)
    # TODO: can be added as last e2e in wallet group (with 5437)
    def test_wallet_offline_can_login_cant_send_transaction(self):
        home = SignInView(self.driver).create_user()
        wallet = home.wallet_button.click()
        wallet.toggle_airplane_mode()
        wallet.accounts_status_account.click_until_presence_of_element(wallet.send_transaction_button)
        send_transaction = wallet.send_transaction_button.click()
        send_transaction.set_recipient_address('0x%s' % basic_user['address'])
        send_transaction.amount_edit_box.set_value("0")
        send_transaction.confirm()
        send_transaction.sign_transaction_button.click()
        if send_transaction.sign_with_password.is_element_displayed():
            self.driver.fail("Sign transaction button is active in offline mode")
        self.driver.close_app()
        self.driver.launch_app()
        SignInView(self.driver).sign_in()
        home.home_button.wait_for_visibility_of_element()
        home.connection_offline_icon.wait_for_visibility_of_element(20)

    @marks.testrail_id(695855)
    @marks.medium
    # TODO: can be split and add as separate group
    def test_custom_gas_settings(self):
        sender = transaction_senders['ETH_7']
        sign_in = SignInView(self.driver)
        sign_in.recover_access(sender['passphrase'])
        wallet = sign_in.wallet_button.click()
        wallet.wait_balance_is_changed()
        wallet.accounts_status_account.click()

        send_transaction = wallet.send_transaction_button.click()
        amount = '0.000%s' % str(random.randint(100000, 999999)) + '1'
        send_transaction.amount_edit_box.set_value(amount)
        send_transaction.set_recipient_address(ens_user_ropsten['ens'])
        send_transaction.next_button.click()
        wallet.ok_got_it_button.wait_and_click(30)
        send_transaction.network_fee_button.click()
        send_transaction = wallet.get_send_transaction_view()
        fee_fields = (send_transaction.per_gas_tip_limit_input, send_transaction.per_gas_price_limit_input)
        [default_tip, default_price] = [field.text for field in fee_fields]
        default_limit = '21000'

        wallet.just_fyi("Check basic validation")
        values = {
            send_transaction.gas_limit_input:
                {
                    'default': default_limit,
                    'value': '22000',
                    '20999': 'wallet-send-min-units',
                    '@!': 'invalid-number',
                },
            send_transaction.per_gas_tip_limit_input:
                {
                    'default': default_tip,
                    'value': '2.5',
                    'aaaa': 'invalid-number',
                },
            send_transaction.per_gas_price_limit_input:
                {
                    'default': default_price,
                    'value': str(round(float(default_price)+3, 9)),
                    '-2': 'invalid-number',
                }
        }
        for field in values:
            for key in values[field]:
                if key != 'default' and key != 'value':
                    field.clear()
                    field.send_keys(key)
                    if not send_transaction.element_by_translation_id(values[field][key]).is_element_displayed(10):
                        self.errors.append("%s is not shown for %s" % (values[field][key], field.accessibility_id))
                    field.clear()
                    field.set_value(values[field]['value'])

        wallet.just_fyi("Set custom fee and check that it will be applied")
        send_transaction.save_fee_button.scroll_and_click()
        if wallet.element_by_translation_id("change-tip").is_element_displayed():
            wallet.element_by_translation_id("continue-anyway").click()
        send_transaction.sign_transaction()
        self.network_api.wait_for_confirmation_of_transaction(sender['address'], amount, confirmations=3)
        transaction = wallet.find_transaction_in_history(amount=amount, return_hash=True)
        expected_params = {
            'fee_cap': values[send_transaction.per_gas_price_limit_input]['value'],
            'tip_cap': '2.5',
            'gas_limit': '22000'
        }
        actual_params = self.network_api.get_custom_fee_tx_params(transaction)
        if actual_params != expected_params:
            self.errors.append('Real params %s for tx do not match expected %s' % (str(actual_params), str(expected_params)))

        wallet.just_fyi('Verify custom fee data on tx screen')
        wallet.swipe_up()
        for key in expected_params:
            if not wallet.element_by_text_part(expected_params[key]).is_element_displayed():
                self.errors.append("Custom tx param %s is not shown on tx history screen" % key)

        wallet.just_fyi("Check below fee popup on mainnet")
        profile = wallet.profile_button.click()
        profile.switch_network()
        sign_in.wallet_button.click()
        wallet.accounts_status_account.click()

        send_transaction = wallet.send_transaction_button.click_until_presence_of_element(send_transaction.amount_edit_box)
        send_transaction.amount_edit_box.set_value(0)
        send_transaction.set_recipient_address(ens_user_ropsten['ens'])
        send_transaction.next_button.click()
        wallet.element_by_translation_id("network-fee").click()
        if not wallet.element_by_translation_id("tx-fail-description2").is_element_displayed():
            self.errors.append("Tx is likely to fail is not shown!")
        if send_transaction.network_fee_button.is_element_displayed():
            self.errors.append("Still can set tx fee when balance is not enough")

        ##  TODO: should be moved to another test after 8f52b9b63ccd9a52b7fe37ab4f89a2e7b6721fcd
        # send_transaction = wallet.get_send_transaction_view()
        # send_transaction.gas_limit_input.clear()
        # send_transaction.gas_limit_input.set_value(default_limit)
        # send_transaction.per_gas_price_limit_input.clear()
        # send_transaction.per_gas_price_limit_input.click()
        # send_transaction.per_gas_price_limit_input.send_keys('1')
        # if not wallet.element_by_translation_id("below-base-fee").is_element_displayed(10):
        #     self.errors.append("Fee is below error is not shown")
        # send_transaction.save_fee_button.scroll_and_click()
        # if not wallet.element_by_translation_id("change-tip").is_element_displayed():
        #     self.errors.append("Popup about changing fee error is not shown")
        # wallet.element_by_translation_id("continue-anyway").click()
        # if not send_transaction.element_by_text_part('0.000021 ETH').is_element_displayed():
        #     self.driver.fail("Custom fee is not applied!")
        self.errors.verify_no_errors()

    @marks.testrail_id(5721)
    # TODO: make a user with 20 contacts, backup contacts and use it in this e2e. cna me merged with other group chat e2e
    def test_cant_add_more_twenty_participants_to_group_chat(self):
        sign_in = SignInView(self.driver)
        home = sign_in.create_user()
        users = [chat_users['A'],
                 chat_users['B'],
                 transaction_senders['ETH_8'],
                 transaction_senders['ETH_1'],
                 transaction_senders['ETH_2'],
                 transaction_senders['ETH_7'],
                 transaction_senders['ETH_STT_3'],
                 transaction_senders['ETH_STT_ADI_1'],
                 transaction_senders['C'],
                 transaction_senders['F'],
                 transaction_senders['G'],
                 transaction_senders['H'],
                 transaction_senders['I'],
                 transaction_senders['M'],
                 transaction_senders['N'],
                 transaction_senders['Q'],
                 transaction_senders['R'],
                 transaction_senders['S'],
                 transaction_senders['T'],
                 transaction_senders['U']]
        usernames = []

        home.just_fyi('Add 20 users to contacts')
        profile = home.profile_button.click()
        profile.contacts_button.click()
        chat = home.get_chat_view()
        for user in users:
            profile.add_new_contact_button.click()
            chat.public_key_edit_box.click()
            chat.public_key_edit_box.set_value(user['public_key'])
            chat.confirm_until_presence_of_element(profile.add_new_contact_button)
            usernames.append(user['username'])

        home.just_fyi('Create group chat with max amount of users')
        profile.home_button.click()
        chat = home.create_group_chat(usernames, 'some_group_chat')

        home.just_fyi('Verify that can not add more users via group info')
        chat.get_back_to_home_view()
        home.get_chat('some_group_chat').click()
        chat.chat_options.click()
        group_info_view = chat.group_info.click()
        if group_info_view.add_members.is_element_displayed():
            self.errors.append('Add members button is displayed when max users are added in chat')
        if not group_info_view.element_by_text_part('20 members').is_element_displayed():
            self.errors.append('Amount of users is not shown on Group info screen')

        self.errors.verify_no_errors()

    @marks.testrail_id(5455)
    def test_recover_accounts_with_certain_seedphrase(self):
        sign_in = SignInView(self.driver)
        for phrase, account in recovery_users.items():
            home_view = sign_in.recover_access(passphrase=phrase, password=unique_password)
            wallet_view = home_view.wallet_button.click()
            address = wallet_view.get_wallet_address()
            if address != account:
                self.errors.append('Restored wallet address "%s" does not match expected "%s"' % (address, account))
            profile = home_view.profile_button.click()
            profile.privacy_and_security_button.click()
            profile.delete_my_profile_button.scroll_and_click()
            profile.delete_my_profile_password_input.set_value(unique_password)
            profile.delete_profile_button.click()
            profile.ok_button.click()
        self.errors.verify_no_errors()
