import requests
import sys
import re

OUTPUT_PATH = '.'
URL_ROOT = 'https://api.constantcontact.com'
AUTH = {'api_key': '', 'access_token': ''}
COLUMNS = ['prefix_name', 'first_name', 'last_name', 'email_addresses',
    'cell_phone', 'home_phone', 'work_phone', 'job_title', 'company_name',
    'fax', 'addresses', 'custom_fields']

def main():
    # get list of contact lists
    url = URL_ROOT + '/v2/lists'
    resp = requests.get(url, params=AUTH)
    if not resp.status_code == 200:
        raise ValueError('Bad response from API: {}'.format(resp.text))

    lists = [(i['id'], i['name']) for i in resp.json()]
    # print('Found {} lists: {}'.format(len(list_ids), list_ids))
    print('Found {} lists'.format(len(lists)))

    next_link = ''
    for l in lists:
        # create a safe filename from the list name
        list_name = "".join([c for c in l[1] if re.match(r'\w', c)])
        print('Building list {}...'.format(list_name))

        # open a file for writing
        fh = open(OUTPUT_PATH + '/' + list_name + '.csv', 'w')
        fh.write(format_header_line())
        fh.close()

        # pagination loop
        page_count = 0
        while True:
            page_count += 1
            url = URL_ROOT + ('/v2/lists/{}/contacts'.format(l[0]) if not next_link else next_link)
            params = AUTH.copy()
            if not next_link:
                params.update({'limit': 500})
            resp = requests.get(url, params=params)
            respobj = resp.json()
            if not resp.status_code == 200:
                raise ValueError('Bad response from API: {}'.format(resp.text))

            if 'next_link' not in respobj['meta']['pagination'].keys():
                break
            next_link = respobj['meta']['pagination']['next_link']

            # write contacts
            with open(OUTPUT_PATH + '/' + list_name + '.csv', 'a') as fh:
                print('   - Writing page {}...'.format(page_count))
                for i in respobj['results']:
                    fh.write(format_contact_line(i))

def format_header_line(columns=COLUMNS):
    return ','.join(columns) + "\n"

def format_contact_line(contact, columns=COLUMNS):
    row_data = {i: (contact[i] if i in contact.keys() else '') for i in columns}

    # special formatting
    row_data['email_addresses'] = format_email_addresses(row_data['email_addresses'])
    row_data['custom_fields'] = format_custom_fields(row_data['custom_fields'])
    row_data['addresses'] = format_addresses(row_data['addresses'])
    row_data['last_name'] = row_data['last_name'].replace("\t", ' ')
    return ','.join([csv_strip(i) for i in row_data.values()]) + "\n"

def csv_strip(s):
    return s.translate({ord(c): None for c in '\t\n;,'})

def format_addresses(addresses):
    r = []
    for i in addresses:
        street_address = i['line1'] if i['line1'] else ''
        street_address += (" " + i['line2'] + " ") if i['line2'] else ''
        street_address += (" " + i['line3'] + " ") if i['line3'] else ''
        r.append("{}: {} {} {} {}".format(
            i['address_type'],
            street_address,
            i['city'],
            i['state_code'],
            i['postal_code']
        ))
    return (' -- '.join(r)).strip()

def format_custom_fields(custom_fields):
    r = ['{}={}'.format(i['label'], i['value']) for i in custom_fields]
    return (', '.join(r)).strip()

def format_email_addresses(emails):
    r = [i['email_address'] for i in emails if i['status'] != 'OPTOUT']
    return (' -- '.join(r)).strip()

if __name__ == '__main__':
    main()
