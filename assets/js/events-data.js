/* ==========================================================
   True Faith Church International — Regional & District events
   ----------------------------------------------------------
   This file holds the EVENTS shown on every region page and
   district page (events-<id>.html) and the event counts on
   the Regional Events and District Events overview cards.
   Edit it to add events; the pages update automatically.

   The list of regions and districts (and their pages) lives in
   tools/content/regions.json and tools/content/districts.json.

   Each region/district has its own id, e.g. 'ashanti-east' or
   'kumasi-district'. Put its events under that id:

     regionalEvents:      upcoming events for a region
     regionalPastEvents:  past events for a region
     districtEvents:      upcoming events for a district
     districtPastEvents:  past events for a district

   EXAMPLE
     regionalPastEvents: {
       'ashanti-east': [
         {
           title: 'Regional Revival Service',
           date:  'Sat 7 Nov 2026 · 9:00 AM',      // shown as written
           place: 'True Faith Church Int., Kumasi', // optional
           image: 'assets/images/my-photo.jpg',     // optional
           link:  'https://...'                     // optional (e.g. photo gallery)
         }
       ]
     }

   - No upcoming events -> "No ... events available at the moment."
   - No past events     -> the "to be confirmed" placeholder cards stay.
   ========================================================== */
window.TFCI_EVENTS = {
  /* No regional or district events have been confirmed yet. */
  regionalEvents: {},
  regionalPastEvents: {},
  districtEvents: {},
  districtPastEvents: {}
};
