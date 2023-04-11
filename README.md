# nb-cdp-discovery
Cisco CDP discovery with Netbox integration. 

This project has many moving parts and needs to be documented.

The concept here is that we have many sites. We can pull site data from Netbox, including a 'CDP Seed Device' to start our scans with. For each site, begin scanning at the site's CDP Seed Device and collect as much data as possible, then correlate that data with the given site. 

This is due for an overhaul. 
