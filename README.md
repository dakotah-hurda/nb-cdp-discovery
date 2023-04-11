# nb-cdp-discovery
Cisco CDP discovery with Netbox integration. 

This project has many moving parts and needs to be documented.

The concept here is that we have many sites. We can pull site data from Netbox, including a 'CDP Seed Device' to start our scans with. For each site, begin scanning at the site's CDP Seed Device and collect as much data as possible, then correlate that data with the given site. 

The CDP Discovery Project was intended to be used as an initial step in discovering all network infrastructure at a given site. Once this bulk data was collected, the next step would be to visit each site and vet all of the imported data, making corrections where necessary. It is not 100% guaranteed that this script will find everything on the network, but it'll do its damned best. 

Be warned that the biggest security flaw in CDP Crawling is that if you happen to find a rogue device exchanging CDP with your equipment, you *will* send your creds directly to that device with this script! This can be somewhat mitigated by operating read-only service accounts, implementing MFA, and enforcing SSH public-key authentication! 
