(function () {
  const root = document.documentElement;
  const shell = document.querySelector(".app-shell");

  const icons = {
    activity: '<path d="M22 12h-4l-3 8-6-16-3 8H2"/>',
    users: '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    coins: '<circle cx="8" cy="8" r="6"/><path d="M18.09 10.37A6 6 0 1 1 10.34 18"/><path d="M7 6h1.5a1.5 1.5 0 0 1 0 3H7V6Z"/><path d="M7 9h2a1.5 1.5 0 0 1 0 3H7V9Z"/>',
    monitor: '<rect x="2" y="4" width="20" height="14" rx="2"/><path d="M8 22h8"/><path d="M12 18v4"/>',
    "monitor-config": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-monitor-cog-icon lucide-monitor-cog"><path d="M12 17v4"/><path d="m14.305 7.53.923-.382"/><path d="m15.228 4.852-.923-.383"/><path d="m16.852 3.228-.383-.924"/><path d="m16.852 8.772-.383.923"/><path d="m19.148 3.228.383-.924"/><path d="m19.53 9.696-.382-.924"/><path d="m20.772 4.852.924-.383"/><path d="m20.772 7.148.924.383"/><path d="M22 13v2a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7"/><path d="M8 21h8"/><circle cx="18" cy="6" r="3"/></svg>',
    table: '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/>',
    globe: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a15 15 0 0 1 0 18"/><path d="M12 3a15 15 0 0 0 0 18"/>',
    syringe: '<path d="m18 2 4 4"/><path d="m17 7 3-3"/><path d="M19 9 8.7 19.3a2.4 2.4 0 0 1-3.4 0l-.6-.6a2.4 2.4 0 0 1 0-3.4L15 5"/><path d="m9 11 4 4"/><path d="m5 19-3 3"/>',
    handshake: '<path d="m11 17 2 2a2.8 2.8 0 0 0 4 0l3-3a2.8 2.8 0 0 0 0-4l-2-2"/><path d="m14 14 2 2"/><path d="m3 12 6-6 4 4-6 6H3v-4Z"/><path d="m14 6 2-2 5 5-2 2"/>',
    headset: '<path d="M3 13a9 9 0 0 1 18 0"/><path d="M21 13v4a2 2 0 0 1-2 2h-2v-6h4Z"/><path d="M3 13v4a2 2 0 0 0 2 2h2v-6H3Z"/><path d="M13 21h3a3 3 0 0 0 3-3"/>',
    wrench: '<path d="M14.7 6.3a4 4 0 0 0-5 5L3 18v3h3l6.7-6.7a4 4 0 0 0 5-5l-2.4 2.4-3-3 2.4-2.4Z"/>',
    hammer: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-hammer-icon lucide-hammer"><path d="m15 12-9.373 9.373a1 1 0 0 1-3.001-3L12 9"/><path d="m18 15 4-4"/><path d="m21.5 11.5-1.914-1.914A2 2 0 0 1 19 8.172v-.344a2 2 0 0 0-.586-1.414l-1.657-1.657A6 6 0 0 0 12.516 3H9l1.243 1.243A6 6 0 0 1 12 8.485V10l2 2h1.172a2 2 0 0 1 1.414.586L18.5 14.5"/></svg>',
    shirt: '<path d="M20.4 7.2 16 4a4 4 0 0 1-8 0L3.6 7.2 6 12l2-1v9h8v-9l2 1 2.4-4.8Z"/>',
    'shopping-cart': '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-shopping-cart-icon lucide-shopping-cart"><circle cx="8" cy="21" r="1"/><circle cx="19" cy="21" r="1"/><path d="M2.05 2.05h2l2.66 12.42a2 2 0 0 0 2 1.58h9.78a2 2 0 0 0 1.95-1.57l1.65-7.43H5.12"/></svg>',
    form: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-form-icon lucide-form"><path d="M4 14h6"/><path d="M4 2h10"/><rect x="4" y="18" width="16" height="4" rx="1"/><rect x="4" y="6" width="16" height="4" rx="1"/></svg>',
    "clipboard-plus": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-clipboard-plus-icon lucide-clipboard-plus"><rect width="8" height="4" x="8" y="2" rx="1" ry="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M9 14h6"/><path d="M12 17v-6"/></svg>',
    "heart-pulse": '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640"><!--!Font Awesome Free v7.3.1 by @fontawesome - https://fontawesome.com License - https://fontawesome.com/license/free Copyright 2026 Fonticons, Inc.--><path d="M320 171.9L305 151.1C280 116.5 239.9 96 197.1 96C123.6 96 64 155.6 64 229.1L64 231.7C64 255.3 70.2 279.7 80.6 304L186.6 304C189.8 304 192.7 302.1 194 299.1L225.8 222.8C229.5 214 238.1 208.2 247.6 208C257.1 207.8 265.9 213.4 269.8 222.1L321.1 336L362.5 253.2C366.6 245.1 374.9 239.9 384 239.9C393.1 239.9 401.4 245 405.5 253.2L428.7 299.5C430.1 302.2 432.8 303.9 435.9 303.9L559.5 303.9C570 279.6 576.1 255.2 576.1 231.6L576.1 229C576 155.6 516.4 96 442.9 96C400.2 96 360 116.5 335 151.1L320 171.8zM533.6 352L435.8 352C414.6 352 395.2 340 385.7 321L384 317.6L341.5 402.7C337.4 411 328.8 416.2 319.5 416C310.2 415.8 301.9 410.3 298.1 401.9L248.8 292.4L238.3 317.6C229.6 338.5 209.2 352.1 186.6 352.1L106.4 352.1C153.6 425.9 229.4 493.8 276.8 530C289.2 539.4 304.4 544.1 319.9 544.1C335.4 544.1 350.7 539.5 363 530C410.6 493.7 486.4 425.8 533.6 352z"/></svg>',
    "heart-hands": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-heart-handshake-icon lucide-heart-handshake"><path d="M19.414 14.414C21 12.828 22 11.5 22 9.5a5.5 5.5 0 0 0-9.591-3.676.6.6 0 0 1-.818.001A5.5 5.5 0 0 0 2 9.5c0 2.3 1.5 4 3 5.5l5.535 5.362a2 2 0 0 0 2.879.052 2.12 2.12 0 0 0-.004-3 2.124 2.124 0 1 0 3-3 2.124 2.124 0 0 0 3.004 0 2 2 0 0 0 0-2.828l-1.881-1.882a2.41 2.41 0 0 0-3.409 0l-1.71 1.71a2 2 0 0 1-2.828 0 2 2 0 0 1 0-2.828l2.823-2.762"/></svg>',
    presentation: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-presentation-icon lucide-presentation"><path d="M2 3h20"/><path d="M21 3v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V3"/><path d="m7 21 5-5 5 5"/></svg>',
    audio: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-volume2-icon lucide-volume-2"><path d="M11 4.702a.705.705 0 0 0-1.203-.498L6.413 7.587A1.4 1.4 0 0 1 5.416 8H3a1 1 0 0 0-1 1v6a1 1 0 0 0 1 1h2.416a1.4 1.4 0 0 1 .997.413l3.383 3.384A.705.705 0 0 0 11 19.298z"/><path d="M16 9a5 5 0 0 1 0 6"/><path d="M19.364 18.364a9 9 0 0 0 0-12.728"/></svg>',
    ticket: '<path d="M2 9a3 3 0 0 0 0 6v3a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-3a3 3 0 0 0 0-6V6a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M13 5v2"/><path d="M13 17v2"/><path d="M13 11v2"/>',
    stethoscope: '<path d="M6 4v6a4 4 0 0 0 8 0V4"/><path d="M4 4h4"/><path d="M12 4h4"/><path d="M10 14v2a4 4 0 0 0 8 0v-1"/><circle cx="19" cy="13" r="2"/>',
    pill: '<path d="m10.5 20.5 10-10a4 4 0 0 0-5.7-5.7l-10 10a4 4 0 0 0 5.7 5.7Z"/><path d="m8.5 11.5 4 4"/>',
    package: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-package-icon lucide-package"><path d="M11 21.73a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73z"/><path d="M12 22V12"/><polyline points="3.29 7 12 12 20.71 7"/><path d="m7.5 4.27 9 5.15"/></svg>',
    box: '<path d="m21 8-9-5-9 5 9 5 9-5Z"/><path d="M3 8v8l9 5 9-5V8"/><path d="M12 13v8"/>',
    boxes: '<path d="M2.97 7.92 12 2.97l9.03 4.95L12 12.97 2.97 7.92Z"/><path d="M2.97 12.92 12 17.97l9.03-5.05"/><path d="M2.97 7.92v10.05L12 23.02l9.03-5.05V7.92"/><path d="M12 12.97v10.05"/><path d="m7.5 5.45 9.03 5.05"/><path d="m16.5 5.45-9.03 5.05"/>',
    briefcase: '<rect x="3" y="7" width="18" height="13" rx="2"/><path d="M8 7V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/><path d="M3 13h18"/>',
    car: '<path d="M5 17h14"/><path d="M6 17v2"/><path d="M18 17v2"/><path d="m4 13 2-6h12l2 6"/><path d="M3 13h18v4H3z"/><circle cx="7" cy="15" r="1"/><circle cx="17" cy="15" r="1"/>',
    ambulance: '<path d="M3 17h18"/><path d="M5 17v2"/><path d="M18 17v2"/><path d="M4 7h9v10H4z"/><path d="M13 10h4l3 3v4h-7z"/><path d="M8.5 9v4"/><path d="M6.5 11h4"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>',
    truck: '<path d="M3 7h11v10H3z"/><path d="M14 10h4l3 3v4h-7z"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/>',
    "heart-pulse": '<path d="M19.5 12.5 12 20l-7.5-7.5a5 5 0 0 1 7-7l.5.5.5-.5a5 5 0 0 1 7 7Z"/><path d="M3 12h4l2-4 3 8 2-4h7"/>',
    flask: '<path d="M9 2h6"/><path d="M10 2v6l-5 9a3 3 0 0 0 2.6 4.5h8.8A3 3 0 0 0 19 17l-5-9V2"/><path d="M7 15h10"/>',
    shield: '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z"/>',
    calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
    "map-pin": '<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    printer: '<path d="M6 9V2h12v7"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/><rect x="6" y="14" width="12" height="8"/>',
    folder: '<path d="M3 5h6l2 2h10v12H3z"/>',
    "file-text": '<path d="M6 2h9l5 5v15H6z"/><path d="M14 2v6h6"/><path d="M9 13h8"/><path d="M9 17h8"/>',
    library: '<path d="M4 3h5v18H4z"/><path d="M10 3h5v18h-5z"/><path d="m16 4 4-1 3 17-4 1z"/>',
    move: '<path d="M5 9 2 12l3 3"/><path d="M9 5 12 2l3 3"/><path d="m15 19-3 3-3-3"/><path d="m19 9 3 3-3 3"/><path d="M2 12h20"/><path d="M12 2v20"/>',
    edit: '<path d="M12 20h9"/><path d="M16.5 3.5a2.1 2.1 0 0 1 3 3L8 18l-4 1 1-4Z"/>',
    "layout-panel-left": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-layout-panel-left-icon lucide-layout-panel-left"><rect width="7" height="18" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/><rect width="7" height="7" x="14" y="14" rx="1"/></svg>',
    "panel-left": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-panel-left-icon lucide-panel-left"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 3v18"/></svg>',
    "panel-left-dashed": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-panel-left-dashed-icon lucide-panel-left-dashed"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M9 14v1"/><path d="M9 19v2"/><path d="M9 3v2"/><path d="M9 9v1"/></svg>',
    image: '<rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><path d="m21 15-5-5L5 21"/>',
    home: '<path d="m3 11 9-8 9 8"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/>',
    menu: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-text-align-justify-icon lucide-text-align-justify"><path d="M3 5h18"/><path d="M3 12h18"/><path d="M3 19h18"/></svg>',
    "menu-dots": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-grip-icon lucide-grip"><circle cx="12" cy="5" r="1"/><circle cx="19" cy="5" r="1"/><circle cx="5" cy="5" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/><circle cx="12" cy="19" r="1"/><circle cx="19" cy="19" r="1"/><circle cx="5" cy="19" r="1"/></svg>',
    list: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-list-icon lucide-list"><path d="M3 5h.01"/><path d="M3 12h.01"/><path d="M3 19h.01"/><path d="M8 5h13"/><path d="M8 12h13"/><path d="M8 19h13"/></svg>',
    theme: '<path d="M12 3a6 6 0 0 0 9 7.2A9 9 0 1 1 12 3Z"/>',
    layout: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-layout-template-icon lucide-layout-template"><rect width="18" height="7" x="3" y="3" rx="1"/><rect width="9" height="7" x="3" y="14" rx="1"/><rect width="5" height="7" x="16" y="14" rx="1"/></svg>',
    "app-window": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-app-window-icon lucide-app-window"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="M10 4v4"/><path d="M2 8h20"/><path d="M6 4v4"/></svg>',
    moon: '<path d="M12 3a6 6 0 0 0 9 7.2A9 9 0 1 1 12 3Z"/>',
    sun: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2"/><path d="M12 20v2"/><path d="m4.93 4.93 1.41 1.41"/><path d="m17.66 17.66 1.41 1.41"/><path d="M2 12h2"/><path d="M20 12h2"/><path d="m6.34 17.66-1.41 1.41"/><path d="m19.07 4.93-1.41 1.41"/>',
    clock: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    bell: '<path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/>',
    history: '<path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><path d="M3 3v5h5"/><path d="M12 7v5l3 2"/>',
    settings: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21h-4v-.09A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3v-4h.09A1.7 1.7 0 0 0 4.6 8.6a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3h4v.09A1.7 1.7 0 0 0 15.4 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 9c.13.38.35.72.64 1 .3.28.7.42 1.1.4H21v4h-.09a1.7 1.7 0 0 0-1.51.6Z"/>',
    filter: '<path d="M3 4h18l-7 8v6l-4 2v-8Z"/>',
    user: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    "circle-user": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-user-round-icon lucide-circle-user-round"><path d="M17.925 20.056a6 6 0 0 0-11.851.001"/><circle cx="12" cy="11" r="4"/><circle cx="12" cy="12" r="10"/></svg>',
    "user-check": '<circle cx="9" cy="8" r="4"/><path d="M2 21a7 7 0 0 1 14 0"/><path d="m16 11 2 2 4-5"/>',
    copy: '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>',
    key: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-key-round-icon lucide-key-round"><path d="M2.586 17.414A2 2 0 0 0 2 18.828V21a1 1 0 0 0 1 1h3a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h1a1 1 0 0 0 1-1v-1a1 1 0 0 1 1-1h.172a2 2 0 0 0 1.414-.586l.814-.814a6.5 6.5 0 1 0-4-4z"/><circle cx="16.5" cy="7.5" r=".5" fill="currentColor"/></svg>',
    logout: '<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><path d="m16 17 5-5-5-5"/><path d="M21 12H9"/>',
    "chevron-down": '<path d="m6 9 6 6 6-6"/>',
    "rotate-right-square": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-rotate-cw-square-icon lucide-rotate-cw-square"><path d="M12 5H6a2 2 0 0 0-2 2v3"/><path d="m9 8 3-3-3-3"/><path d="M4 14v4a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/></svg>',
    search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.35-4.35"/>',
    maximize: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-maximize-icon lucide-maximize"><path d="M8 3H5a2 2 0 0 0-2 2v3"/><path d="M21 8V5a2 2 0 0 0-2-2h-3"/><path d="M3 16v3a2 2 0 0 0 2 2h3"/><path d="M16 21h3a2 2 0 0 0 2-2v-3"/></svg>',
    view: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-view-icon lucide-view"><path d="M21 17v2a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-2"/><path d="M21 7V5a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v2"/><circle cx="12" cy="12" r="1"/><path d="M18.944 12.33a1 1 0 0 0 0-.66 7.5 7.5 0 0 0-13.888 0 1 1 0 0 0 0 .66 7.5 7.5 0 0 0 13.888 0"/></svg>',
    contact: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-contact-icon lucide-contact"><path d="M16 2v2"/><path d="M7 22v-2a2 2 0 0 1 2-2h6a2 2 0 0 1 2 2v2"/><path d="M8 2v2"/><circle cx="12" cy="11" r="3"/><rect x="3" y="4" width="18" height="18" rx="2"/></svg>',
    binoculars: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-binoculars-icon lucide-binoculars"><path d="M10 10h4"/><path d="M19 7V4a1 1 0 0 0-1-1h-2a1 1 0 0 0-1 1v3"/><path d="M20 21a2 2 0 0 0 2-2v-3.851c0-1.39-2-2.962-2-4.829V8a1 1 0 0 0-1-1h-4a1 1 0 0 0-1 1v11a2 2 0 0 0 2 2z"/><path d="M 22 16 L 2 16"/><path d="M4 21a2 2 0 0 1-2-2v-3.851c0-1.39 2-2.962 2-4.829V8a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v11a2 2 0 0 1-2 2z"/><path d="M9 7V4a1 1 0 0 0-1-1H6a1 1 0 0 0-1 1v3"/></svg>',
    "eye-dashed": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-eye-dashed-icon lucide-eye-dashed"><path d="M13.054 18.946a11 11 0 0 1-2.11 0"/><path d="M13.054 5.054a11 11 0 0 0-2.11-.001"/><path d="M17.072 6.274a11 11 0 0 1 1.753 1.173"/><path d="M18.825 16.552a11 11 0 0 1-1.753 1.174"/><path d="M2.514 13.303a11 11 0 0 1-.452-.954 1 1 0 0 1 0-.697 11 11 0 0 1 .45-.955"/><path d="M21.485 10.697a11 11 0 0 1 .453.955 1 1 0 0 1 0 .697 11 11 0 0 1-.453.954"/><path d="M5.173 7.448a11 11 0 0 1 1.753-1.174"/><path d="M6.926 17.726a11 11 0 0 1-1.753-1.174"/><circle cx="12" cy="12" r="3"/></svg>',
    fingerprint: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-fingerprint-pattern-icon lucide-fingerprint-pattern"><path d="M12 10a2 2 0 0 0-2 2c0 1.02-.1 2.51-.26 4"/><path d="M14 13.12c0 2.38 0 6.38-1 8.88"/><path d="M17.29 21.02c.12-.6.43-2.3.5-3.02"/><path d="M2 12a10 10 0 0 1 18-6"/><path d="M2 16h.01"/><path d="M21.8 16c.2-2 .131-5.354 0-6"/><path d="M5 19.5C5.5 18 6 15 6 12a6 6 0 0 1 .34-2"/><path d="M8.65 22c.21-.66.45-1.32.57-2"/><path d="M9 6.8a6 6 0 0 1 9 5.2v2"/></svg>',
    eye: '<path d="M2 12s3.5-6 10-6 10 6 10 6-3.5 6-10 6S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
    eraser: '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-eraser-icon lucide-eraser"><path d="M21 21H8a2 2 0 0 1-1.42-.587l-3.994-3.999a2 2 0 0 1 0-2.828l10-10a2 2 0 0 1 2.829 0l5.999 6a2 2 0 0 1 0 2.828L12.834 21"/><path d="m5.082 11.09 8.828 8.828"/></svg>',
    play: '<path d="m6 3 14 9-14 9V3Z"/>',
    "grid-plus": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-grid2x2-plus-icon lucide-grid-2x2-plus"><path d="M12 3v17a1 1 0 0 1-1 1H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v6a1 1 0 0 1-1 1H3"/><path d="M16 19h6"/><path d="M19 22v-6"/></svg>',
    save: '<path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2Z"/><path d="M17 21v-8H7v8"/><path d="M7 3v5h8"/>',
    "circle-check-big": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-check-big-icon lucide-circle-check-big"><path d="M21.801 10A10 10 0 1 1 17 3.335"/><path d="m9 11 3 3L22 4"/></svg>',
    "certificate-check": '<path d="M7 3h10a2 2 0 0 1 2 2v15l-4-2-3 2-3-2-4 2V5a2 2 0 0 1 2-2Z"/><path d="m8.2 11.7 2.5 2.4 5.1-5.6"/>',
    "badge-check": '<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-badge-check-icon lucide-badge-check"><path d="M3.85 8.62a4 4 0 0 1 4.78-4.77 4 4 0 0 1 6.74 0 4 4 0 0 1 4.78 4.78 4 4 0 0 1 0 6.74 4 4 0 0 1-4.77 4.78 4 4 0 0 1-6.75 0 4 4 0 0 1-4.78-4.77 4 4 0 0 1 0-6.76Z"/><path d="m9 12 2 2 4-4"/></svg>',
    trash: '<path d="M3 6h18"/><path d="M8 6V4h8v2"/><path d="m19 6-1 14H6L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/>',
    "arrow-left": '<path d="m15 18-6-6 6-6"/>',
    "chevrons-left": '<path d="M5 5v14"/><path d="m17 18-6-6 6-6"/>',
    "corner-up-left": '<path d="M9 14 4 9l5-5"/><path d="M4 9h10a6 6 0 0 1 6 6v5"/>',
    "corner-up-right": '<path d="m15 14 5-5-5-5"/><path d="M20 9H10a6 6 0 0 0-6 6v5"/>',
    "undo-2": '<path d="M9 14 4 9l5-5"/><path d="M4 9h9a7 7 0 1 1-5.6 11.2"/>',
    "redo-2": '<path d="m15 14 5-5-5-5"/><path d="M20 9h-9a7 7 0 1 0 5.6 11.2"/>',
    "refresh-cw": '<path d="M21 12a9 9 0 0 1-15 6.7L3 16"/><path d="M3 21v-5h5"/><path d="M3 12a9 9 0 0 1 15-6.7L21 8"/><path d="M21 3v5h-5"/>',
    "arrow-right": '<path d="m9 18 6-6-6-6"/>',
    "arrow-right-to-line": '<path d="M5 12h13"/><path d="m12 5 7 7-7 7"/><path d="M21 5v14"/>',
    "chevrons-right": '<path d="M19 5v14"/><path d="m7 18 6-6-6-6"/>',
    x: '<path d="M18 6 6 18"/><path d="m6 6 12 12"/>',
    check: '<path d="m20 6-11 11-5-5"/>',
    help: '<circle cx="12" cy="12" r="10"/><path d="M9.1 9a3 3 0 1 1 5.8 1c0 2-3 2-3 4"/><path d="M12 17h.01"/>',
    plus: '<path d="M12 5v14"/><path d="M5 12h14"/>',
    minus: '<path d="M5 12h14"/>',
    "ban": '<circle cx="12" cy="12" r="9"/><path d="m7 17 10-10"/>',
  };

  let systemIconSvgs = {};
  try {
    systemIconSvgs = JSON.parse(document.getElementById("system-icon-svgs")?.textContent || "{}");
  } catch (error) {
    systemIconSvgs = {};
  }

  function iconMarkup(name) {
    if (name && systemIconSvgs[name]) return systemIconSvgs[name];
    const body = icons[name] || icons.table;
    return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${body}</svg>`;
  }

  function renderIcons() {
    document.querySelectorAll("[data-nav-icon]").forEach((element) => {
      const name = element.getAttribute("data-nav-icon") || "";
      element.innerHTML = iconMarkup(name);
    });
  }
  window.CelerisRenderIcons = renderIcons;

  function updateThemeToggleIcon() {
    const icon = document.querySelector("[data-theme-toggle] [data-nav-icon]");
    if (!icon) return;
    icon.setAttribute("data-nav-icon", root.classList.contains("dark") ? "sun" : "moon");
  }

  function clearUserRuntimeState() {
    localStorage.removeItem("celeris-tabs");
    Object.keys(localStorage)
      .filter((key) => key.startsWith("celeris-form-state:") || key.startsWith("celeris-tabs"))
      .forEach((key) => localStorage.removeItem(key));
    Object.keys(sessionStorage)
      .filter((key) => key.startsWith("celeris-list-scroll:") || key.startsWith("celeris-open-query") || key.startsWith("celeris-continue") || key.startsWith("celeris:perfil-assistencial:"))
      .forEach((key) => sessionStorage.removeItem(key));
  }

  function setQueryMode(enabled) {
    document.body.classList.toggle("screen-query-mode", enabled);
    setActionStatus(enabled ?"CONSULTA" : "EDIÇÃO");
    const queryButton = document.querySelector("[data-query-toggle]");
    const cancelButton = document.querySelector("[data-query-cancel]");
    if (queryButton) {
      queryButton.dataset.queryMode = enabled ?"execute" : "open";
      queryButton.title = enabled ?"Executar consulta" : "Abrir consulta";
      queryButton.querySelector("[data-nav-icon]").setAttribute("data-nav-icon", enabled ?"play" : "search");
    }
    if (cancelButton) cancelButton.hidden = !enabled;
    document.querySelectorAll("[data-consultable], [data-primary-key]").forEach((field) => {
      const codeOnlyForm = field.closest("[data-query-code-only]");
      const canQuery = codeOnlyForm
        ? field.name === codeOnlyForm.dataset.queryCodeOnly
        : field.dataset.consultable === "true" || field.dataset.primaryKey === "true";
      const canEdit = field.dataset.editable !== "false" && field.dataset.primaryKey !== "true";
      if (enabled && canQuery) {
        field.removeAttribute("readonly");
        field.removeAttribute("disabled");
      } else if (enabled && codeOnlyForm) {
        if (field.matches("select, input[type='checkbox'], input[type='radio']")) {
          field.setAttribute("disabled", "disabled");
        } else {
          field.setAttribute("readonly", "readonly");
        }
      } else if (!enabled && codeOnlyForm && canEdit) {
        field.removeAttribute("readonly");
        field.removeAttribute("disabled");
      } else if (!canEdit) {
        if (field.dataset.primaryKey === "true" || field.matches("select, input[type='checkbox']")) {
          field.setAttribute("disabled", "disabled");
        } else {
          field.setAttribute("readonly", "readonly");
        }
      }
    });
    document.querySelectorAll("[data-query-only='true'], [data-query-only-form] input, [data-query-only-form] select, [data-query-only-form] textarea").forEach((field) => {
      if (enabled) {
        field.removeAttribute("disabled");
        field.removeAttribute("readonly");
      } else if (field.matches("select, input[type='checkbox'], input[type='radio']")) {
        field.setAttribute("disabled", "disabled");
      } else {
        field.setAttribute("readonly", "readonly");
      }
    });
    document.dispatchEvent(new CustomEvent("celeris:query-mode-change", { detail: { enabled } }));
  }

  function clearFormFields(form) {
    clearValidationErrors(form);
    const restoringBeforeClear = isRestoringFormState;
    isRestoringFormState = true;
    form?.querySelectorAll("input, select, textarea").forEach((field) => {
      if (field.type === "hidden") {
        if (field.name !== "csrfmiddlewaretoken") field.value = "";
        return;
      }
      if (field.type === "checkbox" || field.type === "radio") {
        field.checked = false;
        return;
      }
      if (field instanceof HTMLSelectElement) {
        if (field.multiple) {
          Array.from(field.options).forEach((option) => {
            option.selected = false;
          });
        } else {
          field.selectedIndex = 0;
        }
        field.dispatchEvent(new Event("change", { bubbles: true }));
        return;
      }
      field.value = "";
      field.classList.remove("field-invalid", "field-duplicate");
      field.setCustomValidity?.("");
    });
    isRestoringFormState = restoringBeforeClear;
    form?.querySelectorAll("details").forEach((section, index) => {
      section.open = index === 0;
    });
    form?.dispatchEvent(new CustomEvent("celeris:reset-multiselects", { bubbles: true }));
    form?.querySelectorAll("[data-same-address]").forEach((checkbox) => {
      checkbox.checked = false;
      copyResidentialAddressToCommercial(false);
    });
    closeFloatingSelect();
    setQueryMode(false);
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = true;
    form?.setAttribute("data-dirty", "false");
    clearCurrentFormState(form);
    if (form) initialFormSignatures.set(form, formValueSignature(form));
  }

  function clearValidationErrors(scope = document) {
    const rootScope = scope || document;
    rootScope.querySelectorAll(".form-error-summary, .field-error-message, .errorlist").forEach((item) => item.remove());
    rootScope.querySelectorAll(".field-server-invalid, [aria-invalid='true']").forEach((field) => {
      field.classList.remove("field-server-invalid");
      field.removeAttribute("aria-invalid");
    });
    rootScope.querySelectorAll(".field-server-error").forEach((label) => label.classList.remove("field-server-error"));
    document.querySelectorAll("[data-validation-notification]").forEach((item) => item.remove());
    const remainingNotifications = document.querySelectorAll(".notifications-list [data-notification-item]").length;
    const badge = document.querySelector(".notification-badge");
    if (badge) {
      if (remainingNotifications) {
        badge.textContent = String(remainingNotifications);
      } else {
        badge.remove();
        const list = document.querySelector(".notifications-list");
        if (list && !list.querySelector(".notification-empty")) {
          const empty = document.createElement("div");
          empty.className = "notification-empty";
          empty.textContent = "Nenhuma notificação.";
          list.appendChild(empty);
        }
      }
    }
  }

  function clearScreenData() {
    const form = getPrimaryForm();
    if (!form) return;
    clearValidationErrors(form);
    if (form.method?.toLowerCase() === "get") {
      window.location.href = window.location.pathname;
      return;
    }
    if (form.matches("[data-editable-table]")) {
      resetEditableTableRows(form, false);
      form.dataset.dirty = "false";
      window.history.replaceState({}, "", window.location.pathname);
      clearRecordNavigationState();
    } else {
      clearFormFields(form);
      form.querySelectorAll("[data-query-results]").forEach((result) => result.remove());
      window.history.replaceState({}, "", window.location.pathname);
      clearRecordNavigationState();
    }
    setActionStatus("EDIÇÃO");
  }

  function clearRecordNavigationState() {
    ["firstUrl", "previousUrl", "nextUrl", "lastUrl"].forEach((key) => {
      document.body.dataset[key] = "";
    });
    const status = document.querySelector("[data-record-status]");
    if (status) status.textContent = "";
    setupActionButtons();
  }

  function resetEditableTableRows(form, markDirty = false) {
    if (!form?.matches("[data-editable-table]")) return false;
    form.querySelectorAll("tbody tr").forEach((row) => row.remove());
    addEditableTableRow(form, markDirty);
    form.dataset.dirty = markDirty ?"true" : "false";
    updateTablePagerVisibility(form);
    return true;
  }

  function prepareEditableTableQueryRow(form) {
    if (!form?.matches("[data-editable-table]")) return;
    getEditableTableFields(form).forEach((field) => {
      if (field instanceof HTMLSelectElement) {
        if (!Array.from(field.options).some((option) => option.value === "")) {
          field.add(new Option("", ""), 0);
        }
        field.value = "";
      } else if (field.type === "checkbox" || field.type === "radio") {
        field.checked = false;
      } else {
        field.value = "";
      }
      field.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  const savedTheme = localStorage.getItem("celeris-theme");
  if (savedTheme === "dark") root.classList.add("dark");

  if (localStorage.getItem("celeris-sidebar") === "collapsed") {
    shell?.classList.add("sidebar-collapsed");
  }
  root.classList.remove("sidebar-state-collapsed");

  let sidebarFlyout = null;
  let sidebarFlyoutTrigger = null;
  let sidebarFlyoutBackdrop = null;
  let activeLookupField = null;
  let activeFloatingSelect = null;
  let floatingSelectSearch = "";
  let floatingSelectSearchTimer = null;
  let reverseEnterRequested = false;
  let sidebarAutoCollapseTimer = null;
  let isRestoringFormState = false;

  function scheduleSidebarAutoCollapse() {
    window.clearTimeout(sidebarAutoCollapseTimer);
    sidebarAutoCollapseTimer = window.setTimeout(() => {
      shell?.classList.add("sidebar-collapsed");
      localStorage.setItem("celeris-sidebar", "collapsed");
      closeSidebarFlyout();
    }, 10 * 60 * 1000);
  }

  function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, (char) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      "\"": "&quot;",
      "'": "&#39;",
    }[char]));
  }

  function closeSidebarFlyout() {
    sidebarFlyout?.remove();
    sidebarFlyoutBackdrop?.remove();
    sidebarFlyout = null;
    sidebarFlyoutTrigger = null;
    sidebarFlyoutBackdrop = null;
    document.body.classList.remove("sidebar-flyout-open");
  }

  function positionSidebarFlyout(flyout, trigger) {
    const triggerRect = trigger.getBoundingClientRect();
    const viewportGap = 8;
    const availableBelow = Math.max(160, window.innerHeight - Math.max(viewportGap, triggerRect.top) - viewportGap);
    flyout.style.maxHeight = `${availableBelow}px`;
    const flyoutRect = flyout.getBoundingClientRect();
    const left = Math.min(triggerRect.right + viewportGap, window.innerWidth - flyoutRect.width - viewportGap);
    const top = Math.max(viewportGap, Math.min(triggerRect.top, window.innerHeight - flyoutRect.height - viewportGap));
    flyout.style.maxHeight = `${Math.max(120, window.innerHeight - top - viewportGap)}px`;

    flyout.style.left = `${Math.max(viewportGap, left)}px`;
    flyout.style.top = `${top}px`;
  }

  function openSidebarFlyout(navGroup, trigger) {
    const menu = navGroup.querySelector(":scope > div");
    const label = navGroup.querySelector(":scope > summary .nav-label")?.textContent?.trim() || "Menu";
    if (!menu) return;

    if (sidebarFlyout && sidebarFlyoutTrigger === trigger) {
      closeSidebarFlyout();
      return;
    }

    closeSidebarFlyout();
    sidebarFlyoutTrigger = trigger;
    sidebarFlyoutBackdrop = document.createElement("div");
    sidebarFlyoutBackdrop.className = "sidebar-flyout-backdrop";
    document.body.appendChild(sidebarFlyoutBackdrop);
    document.body.classList.add("sidebar-flyout-open");
    sidebarFlyout = document.createElement("div");
    sidebarFlyout.className = "sidebar-flyout";
    const title = document.createElement("div");
    title.className = "sidebar-flyout-title";
    title.textContent = label;
    sidebarFlyout.appendChild(title);
    sidebarFlyout.appendChild(menu.cloneNode(true));
    document.body.appendChild(sidebarFlyout);
    positionSidebarFlyout(sidebarFlyout, trigger);
  }

  function closeSiblingNavGroups(summary) {
    const navGroup = summary.closest(".nav-group");
    if (!navGroup || navGroup.open) return;

    document.querySelectorAll(".sidebar .nav-group[open]").forEach((openGroup) => {
      if (openGroup !== navGroup) openGroup.open = false;
    });
  }

  function ensureLookupModal() {
    let modal = document.querySelector("[data-lookup-modal]");
    if (modal) return modal;

    modal = document.createElement("div");
    modal.className = "lookup-modal";
    modal.dataset.lookupModal = "true";
    modal.hidden = true;
    modal.innerHTML = `
      <div class="lookup-dialog" role="dialog" aria-modal="true" aria-label="Consulta de campo">
        <div class="lookup-header">
          <strong>Consulta</strong>
          <button type="button" data-lookup-close title="Fechar">&times;</button>
        </div>
        <div class="lookup-search">
          <input data-lookup-search type="text" placeholder="Pesquisar">
          <button type="button" data-lookup-run>Consultar</button>
        </div>
        <div class="lookup-results" data-lookup-results></div>
      </div>
    `;
    document.body.appendChild(modal);
    return modal;
  }

  async function runLookup(modal) {
    if (!activeLookupField) return;
    const table = activeLookupField.dataset.lookupTable;
    if (!table) return;
    const search = modal.querySelector("[data-lookup-search]")?.value || "";
    const params = new URLSearchParams({
      table,
      q: search,
      value: activeLookupField.dataset.lookupValueField || "",
      display: activeLookupField.dataset.lookupDisplayField || "",
    });
    const resultsPanel = modal.querySelector("[data-lookup-results]");
    if (resultsPanel) resultsPanel.innerHTML = '<div class="lookup-empty">Consultando...</div>';
    const response = await fetch(`/lookup/?${params.toString()}`);
    const payload = await response.json();
    const results = payload.results || [];
    if (!resultsPanel) return;
    if (!results.length) {
      resultsPanel.innerHTML = '<div class="lookup-empty">Nenhum registro encontrado.</div>';
      return;
    }
    resultsPanel.innerHTML = results.map((item) => `
      <button type="button" data-lookup-select data-value="${escapeHTML(item.value)}">
        <span>${escapeHTML(item.value)}</span>
        <strong>${escapeHTML(item.label)}</strong>
      </button>
    `).join("");
  }

  function openLookup(field) {
    activeLookupField = field;
    const modal = ensureLookupModal();
    const search = modal.querySelector("[data-lookup-search]");
    modal.hidden = false;
    if (search) {
      search.value = field.value || "";
      search.focus();
    }
    runLookup(modal);
  }

  function closeLookup() {
    const modal = document.querySelector("[data-lookup-modal]");
    if (modal) modal.hidden = true;
    activeLookupField = null;
  }

  function setActionStatus(value) {
    const status = document.querySelector("[data-action-status]");
    if (status) status.textContent = value;
  }

  function getPrimaryForm() {
    return document.querySelector(".content form[data-primary-form]") || document.querySelector(".content form");
  }

  const initialFormSignatures = new WeakMap();
  function formValueSignature(form) {
    if (!form) return "";
    return Array.from(form.elements)
      .filter((field) => (
        field.name
        && field.name !== "csrfmiddlewaretoken"
        && field.type !== "hidden"
        && !field.disabled
        && field.dataset.ignoreDirty !== "true"
      ))
      .map((field) => {
        const value = field instanceof HTMLSelectElement && field.multiple
          ?Array.from(field.selectedOptions).map((option) => option.value).join("\u001f")
          : field.value;
        const checked = field.matches?.('input[type="checkbox"], input[type="radio"]') ?field.checked : "";
        return `${field.name}\u001e${field.type || field.tagName}\u001e${checked}\u001e${value ?? ""}`;
      })
      .join("\u001d");
  }
  document.querySelectorAll(".content form").forEach((form) => {
    initialFormSignatures.set(form, formValueSignature(form));
  });
  function formHasActualChanges(form) {
    if (!form) return false;
    if (form.dataset.dirty !== "true") return false;
    const initial = initialFormSignatures.get(form);
    if (initial === undefined) return true;
    return formValueSignature(form) !== initial;
  }

  function hasDirtyForm() {
    return formHasActualChanges(getPrimaryForm());
  }

  function markInvalidFields(form) {
    form?.classList.add("form-submitted");
    const firstInvalid = form?.querySelector(":invalid");
    if (firstInvalid) {
      const section = firstInvalid.closest("details");
      if (section) {
        section.open = true;
        section.dispatchEvent(new CustomEvent("celeris:activate-section", { bubbles: true }));
      }
      window.requestAnimationFrame(() => firstInvalid.focus());
    }
    return Boolean(firstInvalid);
  }

  function setupServerValidationErrors() {
    let errors = {};
    try {
      errors = JSON.parse(document.body.dataset.formErrors || "{}");
    } catch (error) {
      errors = {};
    }
    const firstErrorName = Object.keys(errors)[0];
    if (firstErrorName) {
      const messages = Object.entries(errors)
        .flatMap(([fieldName, fieldErrors]) => {
          const field = document.querySelector(`[name="${CSS.escape(fieldName)}"]`);
          const labelText = field?.closest("label")?.childNodes?.[0]?.textContent?.trim() || fieldName;
          return (fieldErrors || []).map((item) => `${labelText}: ${item.message || item}`);
        });
      if (messages.length) {
        const notificationMessage = `Revise os campos destacados antes de salvar. ${messages.join(" ")}`;
        const item = addNotificationToHistory(notificationMessage, "error", false);
        if (item) item.dataset.validationNotification = "true";
      }
    }
    Object.entries(errors).forEach(([fieldName, fieldErrors]) => {
      const field = document.querySelector(`[name="${CSS.escape(fieldName)}"]`);
      if (!field) return;
      field.classList.add("field-server-invalid");
      field.setAttribute("aria-invalid", "true");
      const label = field.closest("label");
      label?.classList.add("field-server-error");
      if (label && !label.querySelector(".field-error-message, .errorlist")) {
        const message = document.createElement("span");
        message.className = "field-error-message";
        message.setAttribute("role", "tooltip");
        message.textContent = (fieldErrors || []).map((item) => item.message || item).join(" ");
        label.appendChild(message);
      }
    });
    if (!firstErrorName) return;
    const firstField = document.querySelector(`[name="${CSS.escape(firstErrorName)}"]`);
    const section = firstField?.closest("details");
    if (section) {
      section.open = true;
      section.dispatchEvent(new CustomEvent("celeris:activate-section", { bubbles: true }));
    }
    firstField?.scrollIntoView({ behavior: "smooth", block: "center" });
    const blockingNotification = document.querySelector("[data-blocking-notification]");
    if (!blockingNotification || blockingNotification.hidden) {
      window.requestAnimationFrame(() => firstField?.focus());
    }
  }

  function ensureBlockingNotification() {
    let notification = document.querySelector("[data-blocking-notification]");
    if (notification) return notification;

    notification = document.createElement("div");
    notification.className = "blocking-notification";
    notification.dataset.blockingNotification = "true";
    notification.hidden = true;
    notification.innerHTML = `
      <div class="blocking-notification-backdrop" aria-hidden="true"></div>
      <section class="blocking-notification-card" role="dialog" aria-modal="true">
        <strong data-blocking-title>Notificação</strong>
        <p data-blocking-message></p>
        <div class="blocking-notification-extra" data-blocking-extra></div>
        <div class="blocking-notification-actions">
          <button class="toolbar-button" data-blocking-cancel type="button">Cancelar</button>
          <button class="toolbar-button" data-blocking-confirm type="button">OK</button>
        </div>
      </section>
    `;
    document.body.appendChild(notification);
    return notification;
  }

  function addNotificationToHistory(message, type = "info", persist = true) {
    const list = document.querySelector(".notifications-list");
    if (!list) return;
    list.querySelector(".notification-empty")?.remove();
    const item = document.createElement("button");
    item.className = `notification-item ${type}`;
    item.dataset.notificationItem = "true";
    item.type = "button";
    item.innerHTML = `
      <span class="notification-time">${new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}</span>
      <span class="notification-text"></span>
    `;
    item.querySelector(".notification-text").textContent = message;
    list.prepend(item);
    const badge = document.querySelector(".notification-badge");
    if (badge) {
      badge.textContent = String((Number(badge.textContent) || 0) + 1);
    } else {
      const toggle = document.querySelector("[data-notifications-toggle]");
      const newBadge = document.createElement("span");
      newBadge.className = "notification-badge";
      newBadge.textContent = "1";
      toggle?.appendChild(newBadge);
    }
    if (persist) persistNotification(message, type);
    return item;
  }

  function getPersistedNotifications() {
    try {
      return JSON.parse(localStorage.getItem("celeris-notifications") || "[]");
    } catch (error) {
      return [];
    }
  }

  function persistNotification(message, type = "info") {
    const notifications = getPersistedNotifications();
    if (notifications.some((notification) => notification.message === message && notification.type === type)) return;
    notifications.unshift({
      message,
      type,
      time: new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }),
    });
    localStorage.setItem("celeris-notifications", JSON.stringify(notifications.slice(0, 50)));
  }

  function renderPersistedNotifications() {
    const list = document.querySelector(".notifications-list");
    if (!list) return;
    const currentTexts = new Set(Array.from(list.querySelectorAll(".notification-text")).map((item) => item.textContent.trim()));
    getPersistedNotifications().reverse().forEach((notification) => {
      if (currentTexts.has(notification.message)) return;
      list.querySelector(".notification-empty")?.remove();
      const item = document.createElement("button");
      item.className = `notification-item ${notification.type || "info"}`;
      item.dataset.notificationItem = "true";
      item.type = "button";
      item.innerHTML = `
        <span class="notification-time">${escapeHTML(notification.time || "")}</span>
        <span class="notification-text"></span>
      `;
      item.querySelector(".notification-text").textContent = notification.message;
      list.prepend(item);
    });
  }

  function showBlockingNotification(options = {}) {
    const {
      title = "Notificação",
      message = "",
      confirmText = "OK",
      neutralText = "",
      cancelText = "",
      extraElement = null,
      onConfirm = null,
      store = false,
      type = "info",
      focusTarget = null,
      initialFocus = "confirm",
    } = options;
    const notification = ensureBlockingNotification();
    const titleElement = notification.querySelector("[data-blocking-title]");
    const messageElement = notification.querySelector("[data-blocking-message]");
    const extra = notification.querySelector("[data-blocking-extra]");
    const confirmButton = notification.querySelector("[data-blocking-confirm]");
    const cancelButton = notification.querySelector("[data-blocking-cancel]");
    let neutralButton = notification.querySelector("[data-blocking-neutral]");
    if (!neutralButton) {
      neutralButton = document.createElement("button");
      neutralButton.className = "toolbar-button";
      neutralButton.dataset.blockingNeutral = "true";
      neutralButton.type = "button";
      confirmButton.parentElement?.insertBefore(neutralButton, confirmButton);
    }
    const card = notification.querySelector(".blocking-notification-card");

    if (store && message) addNotificationToHistory(message, type);
    if (card) card.dataset.notificationType = type;
    titleElement.textContent = title;
    messageElement.textContent = message;
    extra.innerHTML = "";
    if (extraElement) extra.appendChild(extraElement);
    confirmButton.textContent = confirmText;
    neutralButton.textContent = neutralText || "Descartar";
    neutralButton.hidden = !neutralText;
    cancelButton.textContent = cancelText || "Cancelar";
    cancelButton.hidden = !cancelText;
    notification.hidden = false;

    return new Promise((resolve) => {
      const finish = (result) => {
        notification.hidden = true;
        confirmButton.removeEventListener("click", confirmHandler);
        neutralButton.removeEventListener("click", neutralHandler);
        cancelButton.removeEventListener("click", cancelHandler);
        notification.removeEventListener("keydown", keyHandler);
        extra.innerHTML = "";
        if (focusTarget?.isConnected) {
          window.requestAnimationFrame(() => {
            const section = focusTarget.closest("details");
            if (section) section.open = true;
            focusTarget.focus();
            focusTarget.select?.();
          });
        }
        resolve(result);
      };
      const confirmHandler = () => {
        if (onConfirm && onConfirm() === false) return;
        finish(true);
      };
      const neutralHandler = () => finish(null);
      const cancelHandler = () => finish(false);
      const keyHandler = (event) => {
        if (event.key === "Escape" && !cancelButton.hidden) {
          event.preventDefault();
          cancelHandler();
        }
      };
      confirmButton.addEventListener("click", confirmHandler);
      neutralButton.addEventListener("click", neutralHandler);
      cancelButton.addEventListener("click", cancelHandler);
      notification.addEventListener("keydown", keyHandler);
      window.requestAnimationFrame(() => {
        const firstField = extra.querySelector("select, input, textarea");
        const preferredButton = initialFocus === "cancel" && !cancelButton.hidden ?cancelButton : confirmButton;
        (firstField || preferredButton).focus();
      });
    });
  }

  async function promptUnsavedAction(message) {
    const result = await showBlockingNotification({
      title: "Dados alterados",
      message,
      confirmText: "Salvar",
      neutralText: "Descartar",
      cancelText: "Cancelar",
      initialFocus: "cancel",
    });
    if (result === true) return "save";
    if (result === null) return "discard";
    return "cancel";
  }

  function setupFormConfirmations() {
    document.addEventListener("submit", async (event) => {
      const form = event.target.closest?.("form[data-confirm]");
      if (!form || form.dataset.confirmed === "true") {
        if (form) delete form.dataset.confirmed;
        return;
      }
      event.preventDefault();
      const submitter = event.submitter;
      const confirmed = await showBlockingNotification({
        title: submitter?.title || "Confirmar ação",
        message: form.dataset.confirm,
        confirmText: "Confirmar",
        cancelText: "Cancelar",
        type: "warning",
        initialFocus: "cancel",
      });
      if (!confirmed) return;
      form.dataset.confirmed = "true";
      form.requestSubmit(submitter || undefined);
    }, true);
  }
  window.CelerisPromptUnsavedAction = promptUnsavedAction;

  async function promptChangeReason(form) {
    if (form?.dataset.requiresChangeReason !== "true" || form.dataset.dirty !== "true") return true;
    const reasonField = form.querySelector('[name="motivo_alteracao"]');
    const noteField = form.querySelector('[name="observacao_alteracao"]');
    if (!reasonField || !noteField || (reasonField.value && noteField.value.trim())) return true;

    const extra = document.createElement("div");
    extra.innerHTML = `
      <label>Motivo da alteração
        <select data-change-reason-modal>${reasonField.innerHTML}</select>
      </label>
      <label>Observação
        <input data-change-note-modal type="text" maxlength="255" autocomplete="off">
      </label>
      <span class="blocking-notification-error" data-change-reason-error hidden></span>
    `;
    const select = extra.querySelector("[data-change-reason-modal]");
    const note = extra.querySelector("[data-change-note-modal]");
    const error = extra.querySelector("[data-change-reason-error]");
    select.value = reasonField.value || "";
    note.value = noteField.value || "";

    return showBlockingNotification({
      title: "Motivo da alteração",
      message: "Informe o motivo e a observação para registrar esta alteração.",
      confirmText: "Confirmar",
      cancelText: "Cancelar",
      extraElement: extra,
      onConfirm: () => {
        if (!select.value || !note.value.trim()) {
          error.hidden = false;
          error.textContent = "Preencha o motivo e a observação da alteração.";
          return false;
        }
        reasonField.value = select.value;
        noteField.value = note.value.trim();
        return true;
      },
    });
  }

  async function submitPrimaryForm(form) {
    if (document.body.dataset.canSave !== "true" || form?.dataset.readonlyLock === "true") {
      const message = form?.dataset.lockMessage || "Este registro está bloqueado para edição por outro usuário.";
      addNotificationToHistory(message, "warning", false);
      return false;
    }
    if (!await ensureCurrentRecordLock(form)) return false;
    form?.querySelectorAll("[data-force-submit][disabled]").forEach((field) => {
      field.disabled = false;
    });
    markInvalidFields(form);
    if (!form.reportValidity()) return false;
    if (!await promptChangeReason(form)) return false;
    form.requestSubmit();
    return true;
  }

  function getEditableTableForm() {
    return document.querySelector("form[data-editable-table]");
  }

  function getInlineFormsetTable() {
    return document.querySelector("form[data-primary-form] [data-inline-formset]");
  }

  function getActiveEditableRow() {
    const selected = document.querySelector("tr[data-editable-row].selected:not([hidden])");
    const active = document.activeElement?.closest?.("tr[data-editable-row]:not([hidden])");
    return selected || active;
  }

  function markFormDirty(form) {
    if (!form) return;
    if (document.body.classList.contains("screen-query-mode")) return;
    if (document.body.dataset.canSave !== "true" || form.dataset.readonlyLock === "true") return;
    form.dataset.dirty = "true";
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = false;
    setActionStatus("EDIÇÃO");
  }

  function addEditableTableRow(form, markDirty = true) {
    const template = form.querySelector("template[data-table-new-row]");
    const tbody = form.querySelector("tbody");
    if (!template || !tbody) return false;
    const fragment = template.content.cloneNode(true);
    const row = fragment.querySelector("tr");
    tbody.querySelector(".empty-cell")?.closest("tr")?.remove();
    tbody.appendChild(fragment);
    tbody.querySelectorAll("tr[data-editable-row].selected").forEach((item) => item.classList.remove("selected"));
    row?.classList.add("selected");
    row?.querySelectorAll("[data-cep-state-select]").forEach(filterCepCitiesForState);
    updateTablePagerVisibility(form);
    if (markDirty) {
      markFormDirty(form);
    } else {
      form.dataset.dirty = "false";
      const saveButton = document.querySelector('[data-action="save"]');
      if (saveButton) saveButton.disabled = true;
    }
    row?.querySelector("input:not([readonly]):not([disabled]), select:not([disabled]), textarea:not([readonly]):not([disabled])")?.focus();
    return true;
  }

  function addInlineFormsetRow(table = getInlineFormsetTable(), markDirty = true) {
    const wrapper = table?.closest(".inline-formset-wrapper");
    const template = wrapper?.querySelector("template[data-inline-formset-template]");
    const form = table?.closest("form");
    const totalForms = form?.querySelector('input[name$="-TOTAL_FORMS"]');
    const tbody = table?.querySelector("tbody");
    if (!table || !template || !form || !totalForms || !tbody) return false;
    const index = Number.parseInt(totalForms.value || "0", 10);
    const holder = document.createElement("tbody");
    holder.innerHTML = template.innerHTML.replaceAll("__prefix__", String(index)).trim();
    const row = holder.firstElementChild;
    if (!row) return false;
    tbody.appendChild(row);
    totalForms.value = String(index + 1);
    if (markDirty) markFormDirty(form);
    row.querySelector("input:not([readonly]):not([disabled]), select:not([disabled]), textarea:not([readonly]):not([disabled])")?.focus();
    return true;
  }

  function hasLoadedRecord(form = getPrimaryForm()) {
    if (!form || document.body.classList.contains("screen-query-mode")) return false;
    const primaryKey = form.querySelector('[data-primary-key="true"], .pk-label input');
    return Boolean(primaryKey?.value?.trim());
  }

  function hasSelectedPersistedRow(form = getEditableTableForm()) {
    if (!form || document.body.classList.contains("screen-query-mode")) return false;
    const row = getActiveEditableRow();
    const primaryKey = row?.querySelector('[data-primary-key="true"]');
    return Boolean(row && !row.hidden && primaryKey?.value?.trim());
  }

  function hasSelectedEditableRow(form = getEditableTableForm()) {
    if (!form || document.body.classList.contains("screen-query-mode")) return false;
    const row = getActiveEditableRow();
    return Boolean(row && !row.hidden && form.contains(row));
  }

  function getSelectedRowActiveField(form = getEditableTableForm()) {
    if (!form || document.body.classList.contains("screen-query-mode")) return null;
    const row = getActiveEditableRow();
    if (!row || row.hidden || !form.contains(row)) return null;
    if (!row.querySelector('[data-primary-key="true"]')?.value?.trim()) return null;
    return row.querySelector('select[name^="sn_ativo_"], select[name^="active_"], select[name="new_sn_ativo"], select[name="new_active"]');
  }

  function updateTablePagerVisibility(form = getEditableTableForm()) {
    const pager = form?.querySelector("[data-table-pager]");
    if (!pager) return;
    const visibleRows = Array.from(form.querySelectorAll("tbody tr[data-editable-row]:not([hidden])"));
    const hasLoadedRows = visibleRows.some((row) => row.querySelector('[data-primary-key="true"]')?.value?.trim());
    const hasPageAction = Boolean(pager.querySelector(".table-pager-link:not(.disabled)"));
    pager.hidden = !(hasLoadedRows && hasPageAction);
  }

  function setupInitialEditableRows() {
    if (window.location.search) return;
    document.querySelectorAll("form[data-editable-table]").forEach((form) => {
      if (!form.querySelector("template[data-table-new-row]")) return;
      const hasLoadedRows = Array.from(form.querySelectorAll("tbody tr[data-editable-row]"))
        .some((row) => row.querySelector('[data-primary-key="true"]')?.value?.trim());
      if (hasLoadedRows) return;
      resetEditableTableRows(form, false);
    });
  }

  function removeEditableTableRow(form) {
    const row = getActiveEditableRow();
    if (!form || !row) return false;
    const deleteField = row.querySelector('[data-row-delete]');
    if (deleteField) {
      deleteField.value = "1";
      row.hidden = true;
    } else {
      row.remove();
    }
    markFormDirty(form);
    updateTablePagerVisibility(form);
    setupActionButtons();
    return true;
  }

  function focusEditableTableCell(currentField, direction) {
    const cell = currentField.closest("td");
    const row = currentField.closest("tr");
    const table = currentField.closest("table");
    if (!cell || !row || !table) return false;
    const cellIndex = Array.from(row.children).indexOf(cell);
    const rows = Array.from(table.querySelectorAll("tbody tr[data-editable-row]:not([hidden])"));
    const rowIndex = rows.indexOf(row);
    const nextRow = rows[rowIndex + direction];
    if (!nextRow && direction > 0) {
      const form = currentField.closest("form[data-editable-table]");
      if (form && addEditableTableRow(form)) return true;
    }
    const nextCell = nextRow?.children[cellIndex];
    const nextField = nextCell?.querySelector("input, select, textarea");
    if (!nextField) return false;
    nextField.focus();
    nextField.select?.();
    return true;
  }

  function getEditableTableFields(form) {
    const isQueryMode = document.body.classList.contains("screen-query-mode");
    return Array.from(form?.querySelectorAll("tbody tr[data-editable-row]:not([hidden]) input, tbody tr[data-editable-row]:not([hidden]) select, tbody tr[data-editable-row]:not([hidden]) textarea") || [])
      .filter((field) => {
        if (field.type === "hidden" || field.disabled || field.closest("tr")?.hidden) return false;
        if (field.readOnly && !(isQueryMode && field.dataset.primaryKey === "true")) return false;
        return true;
      });
  }

  function focusEditableTableNextField(currentField, reverse = false) {
    const form = currentField.closest("form[data-editable-table]");
    const fields = getEditableTableFields(form);
    const currentIndex = fields.indexOf(currentField);
    let target = fields[currentIndex + (reverse ?-1 : 1)];
    if (!target && !reverse && !document.body.classList.contains("screen-query-mode") && addEditableTableRow(form)) {
      target = getEditableTableFields(form).find((field) => !field.readOnly);
    }
    target = target || (reverse ?fields[fields.length - 1] : fields[0]);
    if (!target) return false;
    target.focus();
    target.select?.();
    return true;
  }

  async function handleCloseAction() {
    const form = getPrimaryForm();
    if (formHasActualChanges(form)) {
      const action = await promptUnsavedAction("Existem dados digitados. Deseja salvar antes de sair?");
      if (action === "cancel") return;
      if (action === "save") {
        await submitPrimaryForm(form);
        return;
      }
    }
    await releaseCurrentRecordLock();
    if (document.body.dataset.closeMode === "back") {
      window.location.href = document.body.dataset.closeUrl || document.body.dataset.tabKey || "/";
      return;
    }
    closeCurrentTab();
  }

  document.addEventListener("click", async function (event) {
    const receptionPatientSelect = event.target.closest("[data-reception-patient-select]");
    if (receptionPatientSelect && !event.defaultPrevented) {
      event.preventDefault();
      if (receptionPatientSelect.dataset.loading === "true") return;
      receptionPatientSelect.dataset.loading = "true";
      receptionPatientSelect.setAttribute("aria-busy", "true");
      try {
        const response = await fetch(receptionPatientSelect.href, {
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "X-Requested-With": "XMLHttpRequest",
          },
        });
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const payload = await response.json();
        if (payload.confirmacao_necessaria) {
          const confirmed = await showBlockingNotification({
            title: payload.titulo || "Paciente com atendimento em aberto",
            message: payload.mensagem || "Este paciente já possui um atendimento em aberto. Deseja prosseguir?",
            confirmText: "Confirmar",
            cancelText: "Cancelar",
            initialFocus: "cancel",
            type: "warning",
          });
          if (confirmed && payload.prosseguir_url) window.location.href = payload.prosseguir_url;
          return;
        }
        if (payload.redirect_url) window.location.href = payload.redirect_url;
      } catch (error) {
        window.location.href = receptionPatientSelect.href;
      } finally {
        receptionPatientSelect.dataset.loading = "false";
        receptionPatientSelect.removeAttribute("aria-busy");
      }
      return;
    }

    const sidebarDestination = event.target.closest(".sidebar a[href], .sidebar-flyout a[href]");
    if (sidebarDestination && !event.defaultPrevented) {
      shell?.classList.add("sidebar-collapsed");
      localStorage.setItem("celeris-sidebar", "collapsed");
      closeSidebarFlyout();
    }

    const overlayLink = event.target.closest("[data-screen-overlay-link]");
    if (overlayLink) {
      event.preventDefault();
      const overlay = document.querySelector("[data-screen-overlay]");
      const frame = overlay?.querySelector("[data-overlay-frame]");
      const title = overlay?.querySelector("[data-overlay-title]");
      if (overlay && frame) {
        const url = new URL(overlayLink.href, window.location.origin);
        url.searchParams.set("overlay", "1");
        frame.src = url.toString();
        if (title) title.textContent = overlayLink.textContent.trim() || "Cadastro auxiliar";
        overlay.hidden = false;
      }
      return;
    }

    const overlayClose = event.target.closest("[data-overlay-close]");
    if (overlayClose) {
      const overlay = overlayClose.closest("[data-screen-overlay]");
      const frame = overlay?.querySelector("[data-overlay-frame]");
      if (frame) frame.src = "about:blank";
      if (overlay) overlay.hidden = true;
      return;
    }

    const themeButton = event.target.closest("[data-theme-toggle]");
    if (themeButton) {
      root.classList.toggle("dark");
      const theme = root.classList.contains("dark") ?"dark" : "light";
      localStorage.setItem("celeris-theme", theme);
      if (document.body.dataset.username) {
        localStorage.setItem(`celeris-theme-user:${document.body.dataset.username}`, theme);
      }
      updateThemeToggleIcon();
      renderIcons();
      return;
    }

    const sidebarButton = event.target.closest("[data-sidebar-toggle]");
    if (sidebarButton) {
      shell?.classList.toggle("sidebar-collapsed");
      localStorage.setItem("celeris-sidebar", shell.classList.contains("sidebar-collapsed") ?"collapsed" : "expanded");
      closeSidebarFlyout();
      scheduleSidebarAutoCollapse();
      return;
    }

    const queryButton = event.target.closest("[data-query-toggle]");
    if (queryButton) {
      clearValidationErrors(getPrimaryForm() || document);
      const executing = queryButton.dataset.queryMode === "execute";
      const saveButton = document.querySelector('[data-action="save"]');
      const removeButton = document.querySelector('[data-action="remove"]');
      const form = document.querySelector(".content form");
      if (!executing) {
        if (formHasActualChanges(form)) {
          const action = await promptUnsavedAction("Existem dados alterados. Deseja salvar antes de abrir consulta?");
          if (action === "cancel") return;
          if (action === "save") {
            sessionStorage.setItem("celeris-open-query-after-save", "true");
            await submitPrimaryForm(form);
            return;
          }
          await releaseCurrentRecordLock();
          clearFormFields(form);
        }
        await releaseCurrentRecordLock();
        if (false && form?.dataset.dirty === "true") {
          const shouldSave = await showBlockingNotification({
            title: "Dados alterados",
            message: "Existem dados alterados. Deseja salvar antes de abrir consulta?",
            confirmText: "Salvar",
            cancelText: "Não salvar",
          });
          if (shouldSave) {
            sessionStorage.setItem("celeris-open-query-after-save", "true");
            await submitPrimaryForm(form);
            return;
          }
          clearFormFields(form);
        }
        if (form?.matches("[data-editable-table]")) {
          resetEditableTableRows(form, false);
          window.history.replaceState({}, "", window.location.pathname);
        } else {
          clearFormFields(form);
          form?.querySelectorAll("[data-query-results]").forEach((result) => result.remove());
          window.history.replaceState({}, "", window.location.pathname);
          clearRecordNavigationState();
        }
        setQueryMode(true);
        if (form?.matches("[data-editable-table]")) {
          prepareEditableTableQueryRow(form);
          const firstField = getEditableTableFields(form)[0];
          firstField?.focus();
          firstField?.select?.();
        }
        if (saveButton) saveButton.disabled = true;
        if (removeButton) removeButton.disabled = true;
      } else {
        if (form?.method?.toLowerCase() === "get") {
          const queryParameter = form.dataset.queryParameter || "consultar";
          if (queryParameter && !form.elements[queryParameter]) {
            const marker = document.createElement("input");
            marker.type = "hidden";
            marker.name = queryParameter;
            marker.value = "1";
            form.appendChild(marker);
          } else if (queryParameter) {
            form.elements[queryParameter].value = "1";
          }
          form.requestSubmit();
          return;
        }
        const patientQueryTemplate = form?.dataset.patientQueryTemplate;
        const patientCode = form?.querySelector('[name="cd_paciente"]')?.value?.trim();
        if (patientQueryTemplate && patientCode) {
          window.location.href = patientQueryTemplate.replace("__ID__", encodeURIComponent(patientCode));
          return;
        }
        const queryUrl = form?.dataset.queryUrl;
        if (queryUrl) {
          const params = new URLSearchParams();
          params.set("consultar", "1");
          Array.from(form.elements).forEach((field) => {
            if (!field.name || field.type === "hidden" || field.disabled || !String(field.value || "").trim()) return;
            if (field.matches('input[type="checkbox"], input[type="radio"]')) {
              if (field.checked) params.set(field.name, field.value || "true");
            } else if (field instanceof HTMLSelectElement && field.multiple) {
              Array.from(field.selectedOptions).forEach((option) => params.append(field.name, option.value));
            } else {
              params.set(field.name, field.value);
            }
          });
          const queryParameter = form.dataset.queryParameter
            || (["paciente", "prestador", "usuario", "escala"].includes(form.dataset.table) ?"consultar" : "abrir");
          if (queryParameter) {
            params.set(queryParameter, "1");
          }
          clearCurrentFormState(form);
          if (form) form.dataset.dirty = "false";
          window.location.href = `${queryUrl}?${params.toString()}`;
          return;
        }
        if (form?.matches("[data-editable-table]")) {
          const queryValue = Array.from(form.querySelectorAll("input:not([type='hidden']), textarea, select"))
            .filter((field) => field.type !== "color" && !field.readOnly && !field.disabled && String(field.value || "").trim())
            .map((field) => {
              if (field instanceof HTMLSelectElement) return field.value.trim();
              return field.value.trim();
            })[0] || "";
          clearCurrentFormState(form);
          const params = queryValue ?`q=${encodeURIComponent(queryValue)}` : "consultar=1";
          storeCurrentListPosition();
          window.location.href = `${window.location.pathname}?${params}`;
          return;
        }
        setQueryMode(false);
        setupActionButtons();
      }
      renderIcons();
      return;
    }

    const cancelQueryButton = event.target.closest("[data-query-cancel]");
    if (cancelQueryButton) {
      await releaseCurrentRecordLock();
      clearFormFields(getPrimaryForm());
      setupActionButtons();
      renderIcons();
      return;
    }

    const closeAction = event.target.closest('[data-action="close"]');
    if (closeAction) {
      await handleCloseAction();
      return;
    }

    const saveAction = event.target.closest('[data-action="save"]');
    if (saveAction && !saveAction.disabled) {
      const form = getPrimaryForm();
      if (form) {
        storeCurrentListPosition();
        await submitPrimaryForm(form);
      }
      return;
    }

    const newAction = event.target.closest('[data-action="new"]');
    if (newAction && !newAction.disabled) {
      const tableForm = getEditableTableForm();
      if (tableForm && addEditableTableRow(tableForm)) return;
      if (addInlineFormsetRow()) return;
      const targetUrl = document.body.dataset.newUrl;
      if (targetUrl) {
        storeCurrentListPosition();
        const url = new URL(targetUrl, window.location.origin);
        if (url.origin === window.location.origin && !url.searchParams.has("return_to")) {
          url.searchParams.set("return_to", `${window.location.pathname}${window.location.search}`);
        }
        window.location.href = url.toString();
      }
      return;
    }

    const continueAction = event.target.closest('[data-action="continue"]');
    if (continueAction && !continueAction.disabled) {
      const targetUrl = document.body.dataset.continueUrl;
      const form = getPrimaryForm();
      if (targetUrl && formHasActualChanges(form)) {
        const shouldSave = await showBlockingNotification({
          title: "Confirmar dados",
          message: "Existem alterações no cadastro. Deseja salvá-las antes de continuar?",
          confirmText: "Salvar e continuar",
          cancelText: "Cancelar",
        });
        if (shouldSave) {
          sessionStorage.setItem("celeris-continue-after-save", targetUrl);
          await submitPrimaryForm(form);
        }
      } else if (targetUrl) {
        window.location.href = targetUrl;
      }
      return;
    }

    const removeAction = event.target.closest('[data-action="remove"]');
    if (removeAction && !removeAction.disabled) {
      const contextualTarget = document.querySelector("[data-toolbar-remove-target].selected");
      if (contextualTarget) {
        const removeFormId = contextualTarget.dataset.removeForm;
        const removeForm = removeFormId ? document.getElementById(removeFormId) : null;
        const confirmed = await showBlockingNotification({
          title: contextualTarget.dataset.removeTitle || "Excluir registro",
          message: contextualTarget.dataset.removeMessage || "Confirma a exclusão do registro selecionado?",
          confirmText: "Excluir",
          cancelText: "Cancelar",
          type: "warning",
        });
        if (!confirmed || !removeForm) return;
        const resourceField = removeForm.querySelector("[data-remove-resource]");
        if (resourceField) resourceField.value = contextualTarget.dataset.removeResource || "";
        HTMLFormElement.prototype.submit.call(removeForm);
        return;
      }
      const tableForm = getEditableTableForm();
      if (tableForm && removeEditableTableRow(tableForm)) return;
      const form = getPrimaryForm();
      const deleteField = form?.querySelector("[data-record-delete]");
      if (deleteField) {
        const confirmed = await showBlockingNotification({
          title: "Excluir registro",
          message: "Confirma a exclusão deste registro?A alteração será salva imediatamente.",
          confirmText: "Excluir",
          cancelText: "Cancelar",
          type: "warning",
        });
        if (!confirmed) return;
        deleteField.value = "1";
        HTMLFormElement.prototype.submit.call(form);
        return;
      }
    }

    const toggleActiveAction = event.target.closest('[data-action="toggle-active"]');
    if (toggleActiveAction && !toggleActiveAction.disabled) {
      const tableForm = getEditableTableForm();
      const rowActiveField = getSelectedRowActiveField(tableForm);
      if (rowActiveField) {
        rowActiveField.value = rowActiveField.value === "true" ?"false" : "true";
        rowActiveField.dispatchEvent(new Event("change", { bubbles: true }));
        markFormDirty(tableForm);
        setupActionButtons();
        return;
      }
      if (!document.body.dataset.toggleActiveUrl) return;
      const confirmed = await showBlockingNotification({
        title: toggleActiveAction.title,
        message: `Confirma a ação de ${toggleActiveAction.title.toLowerCase()} este cadastro?`,
        confirmText: "Confirmar",
        cancelText: "Cancelar",
      });
      if (!confirmed) return;
      const csrfToken = document.querySelector(".content form [name='csrfmiddlewaretoken']")?.value;
      const response = await fetch(document.body.dataset.toggleActiveUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken || "" },
      });
      if (response.redirected) window.location.href = response.url;
      return;
    }

    const changePasswordAction = event.target.closest('[data-action="change-password"]');
    if (changePasswordAction && !changePasswordAction.disabled && document.body.dataset.passwordUrl) {
      const overlay = document.querySelector("[data-screen-overlay]");
      const frame = overlay?.querySelector("[data-overlay-frame]");
      const title = overlay?.querySelector("[data-overlay-title]");
      if (overlay && frame) {
        const url = new URL(document.body.dataset.passwordUrl, window.location.origin);
        url.searchParams.set("overlay", "1");
        frame.src = url.toString();
        if (title) title.textContent = "Alterar Senha";
        overlay.hidden = false;
      }
      return;
    }

    const reloadAction = event.target.closest('[data-action="reload"]');
    if (reloadAction && !reloadAction.disabled) {
      window.location.href = document.body.dataset.reloadUrl || window.location.href;
      return;
    }

    const printAction = event.target.closest('[data-action="print"]');
    if (printAction && !printAction.disabled && document.body.dataset.printUrl) {
      window.open(document.body.dataset.printUrl, "_blank", "noopener");
      return;
    }

    const clearAction = event.target.closest('[data-action="clear"]');
    if (clearAction && !clearAction.disabled) {
      const form = getPrimaryForm();
      if (formHasActualChanges(form)) {
        const action = await promptUnsavedAction("Existem dados alterados. Deseja salvar antes de limpar a tela?");
        if (action === "cancel") return;
        if (action === "save") {
          await submitPrimaryForm(form);
          return;
        }
      }
      await releaseCurrentRecordLock();
      clearScreenData();
      setupActionButtons();
      renderIcons();
      return;
    }

    const previousAction = event.target.closest('[data-action="previous"]');
    if (previousAction && !previousAction.disabled && document.body.dataset.previousUrl) {
      window.location.href = document.body.dataset.previousUrl;
      return;
    }

    const firstAction = event.target.closest('[data-action="first"]');
    if (firstAction && !firstAction.disabled && document.body.dataset.firstUrl) {
      window.location.href = document.body.dataset.firstUrl;
      return;
    }

    const nextAction = event.target.closest('[data-action="next"]');
    if (nextAction && !nextAction.disabled && document.body.dataset.nextUrl) {
      window.location.href = document.body.dataset.nextUrl;
      return;
    }

    const lastAction = event.target.closest('[data-action="last"]');
    if (lastAction && !lastAction.disabled && document.body.dataset.lastUrl) {
      window.location.href = document.body.dataset.lastUrl;
      return;
    }

    const tabClose = event.target.closest("[data-tab-close]");
    if (tabClose) {
      event.preventDefault();
      event.stopPropagation();
      closeTab(tabClose.dataset.tabUrl, tabClose.dataset.tabKey || tabClose.dataset.tabUrl);
      return;
    }

    const toolbarPrintTarget = event.target.closest("[data-toolbar-print-url]");
    if (toolbarPrintTarget) {
      document.body.dataset.printUrl = toolbarPrintTarget.dataset.toolbarPrintUrl || "";
      document.querySelectorAll("[data-toolbar-print-url].is-selected").forEach((row) => {
        if (row !== toolbarPrintTarget) row.classList.remove("is-selected");
      });
      toolbarPrintTarget.classList.add("is-selected");
      setupActionButtons();
      renderIcons();
      if (event.target.closest("button, a, input, select, textarea, form")) return;
    }

    const lookupTrigger = event.target.closest("[data-lookup-trigger]");
    if (lookupTrigger) {
      const field = lookupTrigger.closest(".field-lookup-wrap")?.querySelector("[data-lookup-table]");
      if (field) openLookup(field);
      return;
    }

    const lookupClose = event.target.closest("[data-lookup-close]");
    if (lookupClose) {
      closeLookup();
      return;
    }

    const lookupRun = event.target.closest("[data-lookup-run]");
    if (lookupRun) {
      runLookup(lookupRun.closest("[data-lookup-modal]"));
      return;
    }

    const lookupSelect = event.target.closest("[data-lookup-select]");
    if (lookupSelect && activeLookupField) {
      activeLookupField.value = lookupSelect.dataset.value || "";
      activeLookupField.dispatchEvent(new Event("input", { bubbles: true }));
      closeLookup();
      return;
    }

    const notificationsToggle = event.target.closest("[data-notifications-toggle]");
    if (notificationsToggle) {
      const panel = document.querySelector("[data-notifications-panel]");
      if (panel) panel.hidden = !panel.hidden;
      return;
    }

    const notificationsClear = event.target.closest("[data-notifications-clear]");
    if (notificationsClear) {
      localStorage.removeItem("celeris-notifications");
      const empty = document.createElement("div");
      empty.className = "notification-empty";
      empty.textContent = "Nenhuma notificação.";
      document.querySelector(".notifications-list")?.replaceChildren(empty);
      document.querySelector(".notification-badge")?.remove();
      return;
    }

    const notificationItem = event.target.closest("[data-notification-item]");
    if (notificationItem) {
      notificationItem.classList.toggle("open");
      return;
    }

    const collapsedSummary = event.target.closest(".sidebar .nav-group > summary");
    if (collapsedSummary && shell?.classList.contains("sidebar-collapsed")) {
      event.preventDefault();
      openSidebarFlyout(collapsedSummary.closest(".nav-group"), collapsedSummary);
      scheduleSidebarAutoCollapse();
      return;
    }

    if (collapsedSummary) {
      closeSidebarFlyout();
      closeSiblingNavGroups(collapsedSummary);
      scheduleSidebarAutoCollapse();
      return;
    }

    if (sidebarFlyout && !event.target.closest(".sidebar-flyout")) {
      closeSidebarFlyout();
    }
    const floatingSourceId = activeFloatingSelect?.dataset.fieldId;
    const clickedFloatingSource = floatingSourceId && event.target.closest(`#${CSS.escape(floatingSourceId)}`);
    if (activeFloatingSelect && !event.target.closest("[data-floating-select]") && !clickedFloatingSource) {
      closeFloatingSelect();
    }

    const editableCell = event.target.closest("form[data-editable-table] td");
    if (editableCell) {
      editableCell.closest("tbody")?.querySelectorAll("tr.selected").forEach((row) => row.classList.remove("selected"));
      editableCell.closest("tr[data-editable-row]")?.classList.add("selected");
      setupActionButtons();
    }

    const contextualRemoveTarget = event.target.closest("[data-toolbar-remove-target]");
    if (contextualRemoveTarget) {
      document.querySelectorAll("[data-toolbar-remove-target].selected").forEach((target) => {
        if (target !== contextualRemoveTarget) target.classList.remove("selected");
      });
      contextualRemoveTarget.classList.toggle("selected");
      setupActionButtons();
    } else if (!event.target.closest('[data-action="remove"]')) {
      document.querySelectorAll("[data-toolbar-remove-target].selected").forEach((target) => target.classList.remove("selected"));
      setupActionButtons();
    }

    const notificationsPanel = document.querySelector("[data-notifications-panel]");
    if (notificationsPanel && !notificationsPanel.hidden && !event.target.closest("[data-notifications-panel]")) {
      notificationsPanel.hidden = true;
    }
  });

  document.addEventListener("contextmenu", function (event) {
    const allowedContextArea = event.target.closest(
      "[data-allow-context-menu], .document-studio, [data-profile-context-menu], [data-profile-list], .sidebar, .sidebar-flyout"
    );
    if (!allowedContextArea) {
      event.preventDefault();
    }
  });

  document.addEventListener("pointerdown", function (event) {
    const select = event.target.closest(".content select, .pep-standalone-main select");
    if (
      !select
      || select.disabled
      || select.matches("[data-native-select]")
      || select.closest("[data-blocking-notification]")
    ) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    if (activeFloatingSelect?.dataset.fieldId === select.id && activeFloatingSelect.isConnected) {
      positionFloatingSelect(activeFloatingSelect, select);
      return;
    }
    openFloatingSelect(select);
  });

  document.addEventListener("click", function (event) {
    const select = event.target.closest(".content select, .pep-standalone-main select");
    if (!select || select.matches("[data-native-select]") || select.closest("[data-blocking-notification]")) return;
    event.preventDefault();
    event.stopImmediatePropagation();
  });

  document.addEventListener("submit", async function (event) {
    const form = event.target;
    if (form.dataset.confirmMessage && form.dataset.confirmed !== "true") {
      event.preventDefault();
      const confirmed = await showBlockingNotification({
        title: form.dataset.confirmTitle || "Confirmar ação",
        message: form.dataset.confirmMessage,
        confirmText: form.dataset.confirmText || "Confirmar",
        cancelText: "Cancelar",
        type: "warning",
        initialFocus: "cancel",
      });
      if (confirmed) {
        form.dataset.confirmed = "true";
        form.requestSubmit(event.submitter || undefined);
        window.setTimeout(() => {
          delete form.dataset.confirmed;
        }, 0);
      }
      return;
    }
    if (form.matches("[data-clear-tabs]")) {
      clearUserRuntimeState();
    }
    if (form.matches(".content form") && form.method?.toLowerCase() !== "get") {
      clearCurrentFormState(form);
    }
    if (form.matches(".content form")) markInvalidFields(form);
  });

  document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") {
      const overlay = document.querySelector("[data-screen-overlay]:not([hidden])");
      if (overlay) {
        const frame = overlay.querySelector("[data-overlay-frame]");
        if (frame) frame.src = "about:blank";
        overlay.hidden = true;
        return;
      }
      reverseEnterRequested = true;
      closeLookup();
      closeFloatingSelect();
      window.setTimeout(() => {
        reverseEnterRequested = false;
      }, 1200);
      return;
    }

    if (event.key === "Tab" && event.target.matches(".generated-clinical-form input, .generated-clinical-form select, .generated-clinical-form textarea")) {
      const formGrid = event.target.closest(".generated-clinical-form");
      const gridItems = Array.from(formGrid.children);
      const visualFields = Array.from(formGrid.querySelectorAll("input, select, textarea"))
        .filter((field) => field.type !== "hidden" && !field.disabled && !field.readOnly && field.offsetParent !== null)
        .sort((left, right) => {
          const ownerFor = (field) => {
            let owner = field;
            while (owner.parentElement && owner.parentElement !== formGrid) owner = owner.parentElement;
            return owner;
          };
          const coordinate = (field) => {
            const owner = ownerFor(field);
            const style = getComputedStyle(owner);
            const row = Number.parseInt(style.gridRowStart, 10);
            const column = Number.parseInt(style.gridColumnStart, 10);
            return {
              row: Number.isFinite(row) ?row : gridItems.indexOf(owner) + 1,
              column: Number.isFinite(column) ?column : 1,
            };
          };
          const leftPosition = coordinate(left);
          const rightPosition = coordinate(right);
          return leftPosition.row - rightPosition.row || leftPosition.column - rightPosition.column;
        });
      const currentIndex = visualFields.indexOf(event.target);
      if (currentIndex >= 0 && visualFields.length) {
        event.preventDefault();
        closeFloatingSelect();
        const direction = event.shiftKey ?-1 : 1;
        const nextIndex = (currentIndex + direction + visualFields.length) % visualFields.length;
        focusField(visualFields[nextIndex]);
      }
      return;
    }

    if (
      /^[1-6]$/.test(event.key)
      && document.querySelector(".provider-form")
      && !event.ctrlKey
      && !event.altKey
      && !event.metaKey
      && !event.target.matches("input, select, textarea, button, [contenteditable='true']")
    ) {
      const section = document.querySelector(`[data-provider-section="${event.key}"]`);
      if (section) {
        event.preventDefault();
        section.open = true;
        section.scrollIntoView({ behavior: "smooth", block: "start" });
        const firstField = Array.from(section.querySelectorAll("input, select, textarea"))
          .find((field) => field.type !== "hidden" && !field.disabled && !field.readOnly);
        window.setTimeout(() => focusField(firstField), 180);
      }
      return;
    }

    if (event.key === "ArrowDown" && event.target.matches("form[data-editable-table] input, form[data-editable-table] select, form[data-editable-table] textarea")) {
      if (!event.target.matches("select")) {
        event.preventDefault();
        focusEditableTableCell(event.target, 1);
      }
      return;
    }
    if (event.key === "ArrowUp" && event.target.matches("form[data-editable-table] input, form[data-editable-table] select, form[data-editable-table] textarea")) {
      if (!event.target.matches("select")) {
        event.preventDefault();
        focusEditableTableCell(event.target, -1);
      }
      return;
    }
    if (event.key === "Enter" && event.target.matches("[data-lookup-search]")) {
      event.preventDefault();
      runLookup(event.target.closest("[data-lookup-modal]"));
    }
    if (event.key === "Enter" && event.target.matches("form[data-editable-table] input, form[data-editable-table] select, form[data-editable-table] textarea")) {
      event.preventDefault();
      focusEditableTableNextField(event.target, event.shiftKey || reverseEnterRequested);
      reverseEnterRequested = false;
      return;
    }
    if (event.key === "Tab" && event.target.matches("form[data-editable-table] input, form[data-editable-table] select, form[data-editable-table] textarea")) {
      event.preventDefault();
      focusEditableTableNextField(event.target, event.shiftKey);
      return;
    }
    if (
      event.target.matches(".content select")
      && (
        event.key === "Enter"
        || event.key === "ArrowDown"
        || event.key === "ArrowUp"
        || (event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey)
      )
    ) {
      event.preventDefault();
      const field = event.target;
      const isCurrentFloatingSelect = getFloatingSelectField() === field;
      if (!isCurrentFloatingSelect) openFloatingSelect(field);
      if (event.key === "Enter" && isCurrentFloatingSelect) {
        activeFloatingSelect?.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter", bubbles: true }));
      } else if (event.key === "ArrowDown" || event.key === "ArrowUp" || event.key.length === 1) {
        window.setTimeout(() => {
          activeFloatingSelect?.dispatchEvent(new KeyboardEvent("keydown", { key: event.key, bubbles: true }));
        });
      }
      return;
    }
    if (
      event.key === "Enter"
      && event.target.matches(".content textarea")
      && event.target.closest(".generated-clinical-form, [data-document-fill-form]")
    ) {
      return;
    }
    if (event.key === "Enter" && event.target.matches(".content input, .content select, .content textarea")) {
      const field = event.target;
      event.preventDefault();
      if (event.shiftKey || reverseEnterRequested) {
        reverseEnterRequested = false;
        focusPreviousField(field);
      } else {
        focusNextField(field);
      }
    }
    if (event.key === "Tab" && !event.shiftKey && event.target.matches(".content input, .content select, .content textarea")) {
      const field = event.target;
      const visibleFields = getNavigableFields().filter((input) => input.offsetParent !== null);
      if (visibleFields[visibleFields.length - 1] === field) {
        event.preventDefault();
        focusNextField(field);
      }
    }
  });

  function getNavigableFields(includeClosed = false) {
    return Array.from(document.querySelectorAll(".content input, .content select, .content textarea"))
      .filter((field) => {
        if (field.closest("[hidden]")) return false;
        if (field.type === "hidden" || field.disabled || field.readOnly) return false;
        return includeClosed || field.offsetParent !== null;
      });
  }

  function focusNextField(currentField) {
    const fields = getNavigableFields(true);
    const currentIndex = fields.indexOf(currentField);
    let nextField = fields[currentIndex + 1];
    const nextSection = nextField?.closest("details");
    const currentSection = currentField.closest("details");
    if (nextSection && nextSection !== currentSection) {
      nextSection.open = true;
    }
    nextField = nextField || fields[0];
    if (!nextField) return;
    window.requestAnimationFrame(() => focusField(nextField));
  }

  function focusPreviousField(currentField) {
    const fields = getNavigableFields(true);
    const currentIndex = fields.indexOf(currentField);
    let previousField = fields[currentIndex - 1];
    previousField = previousField || fields[fields.length - 1];
    const previousSection = previousField?.closest("details");
    if (previousSection) previousSection.open = true;
    if (!previousField) return;
    window.requestAnimationFrame(() => focusField(previousField));
  }

  function closeFloatingSelect() {
    activeFloatingSelect?.remove();
    activeFloatingSelect = null;
    floatingSelectSearch = "";
    window.clearTimeout(floatingSelectSearchTimer);
  }

  function getFloatingSelectField() {
    const fieldId = activeFloatingSelect?.dataset.fieldId;
    return fieldId ?document.getElementById(fieldId) : null;
  }

  function positionFloatingSelect(panel, field) {
    const rect = field.getBoundingClientRect();
    const gap = 4;
    const viewportGap = 8;
    const width = Math.max(rect.width, 180);
    const spaceBelow = Math.max(0, window.innerHeight - rect.bottom - gap - viewportGap);
    const spaceAbove = Math.max(0, rect.top - gap - viewportGap);
    const preferredHeight = Math.min(panel.scrollHeight || 260, 320);
    const openBelow = spaceBelow >= Math.min(preferredHeight, 180) || spaceBelow >= spaceAbove;
    const availableHeight = Math.max(96, openBelow ?spaceBelow : spaceAbove);
    const panelHeight = Math.min(preferredHeight, availableHeight);
    const maxLeft = Math.max(viewportGap, window.innerWidth - width - viewportGap);
    const left = Math.max(viewportGap, Math.min(rect.left, maxLeft));
    const top = openBelow ?rect.bottom + gap : rect.top - gap - panelHeight;
    panel.style.width = `${width}px`;
    panel.style.maxHeight = `${availableHeight}px`;
    panel.style.left = `${left}px`;
    panel.style.top = `${Math.max(viewportGap, Math.min(top, window.innerHeight - panelHeight - viewportGap))}px`;
    panel.dataset.placement = openBelow ?"bottom" : "top";
  }

  function openFloatingSelect(field) {
    closeFloatingSelect();
    const options = Array.from(field.options).filter((option) => !option.disabled);
    if (!options.length) return;
    const panel = document.createElement("div");
    panel.className = "floating-select-panel";
    panel.dataset.floatingSelect = "true";
    if (!field.id) field.id = `floating-select-${Date.now()}`;
    panel.dataset.fieldId = field.id;
    panel.innerHTML = options.map((option, index) => {
      const isEmpty = !option.value && !(option.text || "").trim();
      const optionIcon = option.dataset.iconKey;
      return `
      <button type="button" data-select-index="${index}" ${isEmpty ?'data-empty-option="true"' : ""} class="${option.selected ?"active" : ""}${optionIcon ?" has-icon" : ""}">
        ${optionIcon ?`<span class="floating-select-icon" aria-hidden="true">${iconMarkup(optionIcon)}</span>` : ""}
        <span>${escapeHTML(option.text || option.value || "EM BRANCO")}</span>
      </button>
    `;
    }).join("");
    const panelHost = field.closest("dialog[open]") || document.body;
    panelHost.appendChild(panel);
    activeFloatingSelect = panel;
    positionFloatingSelect(panel, field);
    const setActiveOption = (button) => {
      if (!button) return;
      panel.querySelectorAll("button").forEach((item) => item.classList.remove("active"));
      button.classList.add("active");
      button.scrollIntoView({ block: "nearest" });
    };
    const selectOption = (button) => {
      const option = options[Number(button.dataset.selectIndex)];
      if (!option) return;
      if (field.multiple) {
        option.selected = !option.selected;
        button.classList.toggle("active", option.selected);
        field.dispatchEvent(new Event("change", { bubbles: true }));
        return;
      }
      field.value = option.value;
      field.dispatchEvent(new Event("change", { bubbles: true }));
      closeFloatingSelect();
      focusNextField(field);
    };
    panel.addEventListener("mousedown", (event) => {
      if (event.target.closest("button")) event.preventDefault();
    });
    panel.addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (button) selectOption(button);
    });
    panel.addEventListener("keydown", (event) => {
      const buttons = Array.from(panel.querySelectorAll("button"));
      const current = document.activeElement.closest?.("button") || panel.querySelector("button.active");
      const currentIndex = Math.max(buttons.indexOf(current), 0);
      if (event.key === "ArrowDown") {
        event.preventDefault();
        const nextButton = buttons[Math.min(currentIndex + 1, buttons.length - 1)];
        setActiveOption(nextButton);
        nextButton?.focus();
      } else if (event.key === "ArrowUp") {
        event.preventDefault();
        const previousButton = buttons[Math.max(currentIndex - 1, 0)];
        setActiveOption(previousButton);
        previousButton?.focus();
      } else if (event.key === "Enter") {
        event.preventDefault();
        if (event.shiftKey || reverseEnterRequested) {
          reverseEnterRequested = false;
          closeFloatingSelect();
          focusPreviousField(field);
        } else {
          selectOption(current || panel.querySelector("button.active") || buttons[0]);
        }
      } else if (event.key === "Tab") {
        event.preventDefault();
        closeFloatingSelect();
        if (event.shiftKey) {
          focusPreviousField(field);
        } else {
          focusNextField(field);
        }
      } else if (event.key === "Escape") {
        closeFloatingSelect();
        field.focus();
      } else if (event.key.length === 1 && !event.ctrlKey && !event.altKey && !event.metaKey) {
        floatingSelectSearch += event.key.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toUpperCase();
        window.clearTimeout(floatingSelectSearchTimer);
        floatingSelectSearchTimer = window.setTimeout(() => {
          floatingSelectSearch = "";
        }, 900);
        const match = buttons.find((button) => (
          button.textContent || ""
        ).normalize("NFD").replace(/[\u0300-\u036f]/g, "").trim().toUpperCase().startsWith(floatingSelectSearch));
        if (match) {
          event.preventDefault();
          setActiveOption(match);
          match.focus();
        }
      }
    });
    window.requestAnimationFrame(() => {
      const activeButton = panel.querySelector("button.active:not([data-empty-option='true'])")
        || panel.querySelector("button:not([data-empty-option='true'])")
        || panel.querySelector("button");
      setActiveOption(activeButton);
      activeButton?.focus();
    });
  }

  function focusField(field) {
    field.focus();
    if (field instanceof HTMLInputElement) field.select?.();
  }

  window.addEventListener("resize", () => {
    closeSidebarFlyout();
    closeFloatingSelect();
  });
  window.addEventListener("scroll", (event) => {
    const scrollTarget = event.target;
    if (!(scrollTarget instanceof Element) || !scrollTarget.closest(".sidebar-flyout")) {
      closeSidebarFlyout();
    }
    if (activeFloatingSelect) {
      const fieldId = activeFloatingSelect.dataset.fieldId;
      const field = fieldId ?document.getElementById(fieldId) : null;
      if (field) positionFloatingSelect(activeFloatingSelect, field);
    }
  }, true);

  function normalizeFieldName(value) {
    return value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-zA-Z0-9_]+/g, "_")
      .replace(/^_+|_+$/g, "")
      .toUpperCase();
  }

  function normalizeTextValue(value) {
    return value
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .replace(/[^a-zA-Z0-9_% ]+/g, "")
      .toUpperCase();
  }

  const fieldColumnAliases = {
    pergunta_classificacao: { _pk: "cd_pergunta_classificacao", name: "nm_pergunta", type: "tp_resposta", order: "nr_ordem", required: "sn_obrigatoria", active: "sn_ativo" },
    fluxo_classificacao: { _pk: "cd_fluxo_classificacao", group: "nm_grupo", name: "nm_fluxo", guidance: "ds_orientacao", color: "cd_cor_recomendada", order: "nr_ordem", active: "sn_ativo" },
    cor_classificacao_risco: { _pk: "cd_cor_classificacao", code: "cd_cor", name: "nm_cor", hex: "ds_cor_hex", priority: "nr_prioridade", active: "sn_ativo" },
    protocolo_senha: { _pk: "cd_protocolo_senha", acronym: "sg_protocolo", name: "nm_protocolo", description: "ds_protocolo", active: "sn_ativo" },
    icone_chamada: { _pk: "cd_icone_chamada", name: "nm_icone", svg: "ds_svg", active: "sn_ativo" },
    regra_subdivisao_senha: { rule_name: "cd_classe_senha", rule_acronym: "sg_regra", rule_priority: "nr_prioridade", rule_min_age: "nr_idade_minima", rule_max_age: "nr_idade_maxima", rule_protocol: "cd_protocolo", rule_timeout: "nr_tempo_limite", rule_icon: "cd_icone_chamada", rule_active: "sn_ativo" },
  };

  function updateFieldStatus(field) {
    const status = document.querySelector("[data-field-status]");
    if (!status) return;

    if (!field) {
      status.textContent = "";
      return;
    }

    const labelText = field.closest("label")?.childNodes?.[0]?.textContent?.trim() || "";
    const businessLabel = labelText || field.getAttribute("aria-label") || field.placeholder || "Campo";
    const owner = field.closest("form[data-table], section[data-table], details[data-table]");
    const tableName = field.dataset.fieldTable || owner?.dataset.table;
    const rawFieldName = field.dataset.fieldName || field.name || "";
    const normalizedFieldName = rawFieldName.replace(/^new_/, "").replace(/_\d+$/, "");
    const aliases = fieldColumnAliases[tableName] || {};
    const fieldName = field.dataset.fieldName
      || aliases[normalizedFieldName]
      || (field.dataset.primaryKey === "true" ? aliases._pk : "")
      || normalizedFieldName;
    const isExactTableField = Boolean(
      tableName
      && fieldName
      && (field.dataset.fieldTable || (
        owner
        && (owner.tagName !== "FORM" || owner.method?.toLowerCase() !== "get")
      ))
      && field.type !== "hidden"
    );
    status.textContent = isExactTableField
      ?`${normalizeFieldName(tableName)}.${normalizeFieldName(fieldName)}`
      : businessLabel.trim();
  }

  function normalizeInputValue(field) {
    if (!(field instanceof HTMLInputElement || field instanceof HTMLTextAreaElement)) return;
    if (field.dataset.mask || field.matches("[data-svg-source], [data-preserve-characters]")) return;
    if (field.closest(".generated-clinical-form, [data-document-fill-form]")) return;
    const type = field.type || "";
    if (["password", "email", "url", "number", "date", "time", "datetime-local", "month", "week", "color"].includes(type)) return;
    const start = field.selectionStart;
    const end = field.selectionEnd;
    field.value = normalizeTextValue(field.value);
    if (typeof start === "number" && typeof end === "number") {
      field.setSelectionRange(start, end);
    }
  }

  document.addEventListener("focusin", function (event) {
    const field = event.target.closest("input, select, textarea");
    if (field) updateFieldStatus(field);
  });

  document.addEventListener("focusout", function (event) {
    return;
  });

  document.addEventListener("input", async function (event) {
    const field = event.target.closest("input, textarea");
    if (!field) return;
    if (!event.isTrusted && field.closest("[data-document-editor-form]")) return;
    if (!field.closest("[data-preserve-input]")) {
      normalizeInputValue(field);
    }
    if (field.matches("[data-war-name]")) {
      field.dataset.manuallyEdited = "true";
    }
    if (field.matches("[data-war-name-source]")) {
      const warNameField = document.querySelector("[data-war-name]");
      const providerForm = field.closest(".provider-form");
      const isNewProvider = providerForm && !providerForm.dataset.providerId;
      const isQueryMode = document.body.classList.contains("screen-query-mode");
      if (warNameField && isNewProvider && !isQueryMode && !warNameField.dataset.manuallyEdited) {
        window.clearTimeout(field.celerisWarNameTimer);
        field.celerisWarNameTimer = window.setTimeout(() => {
          const nameParts = field.value.trim().split(/\s+/).filter(Boolean);
          warNameField.value = nameParts.length > 1
            ? `${nameParts[0]} ${nameParts.at(-1)}`
            : (nameParts[0] || "");
          warNameField.dispatchEvent(new Event("change", { bubbles: true }));
        }, 700);
      }
    }
    if (field.dataset.mask === "cpf") {
      field.value = formatCPF(field.value);
    } else if (field.dataset.mask === "celular") {
      field.value = formatCellphone(field.value);
    }
    if (isRestoringFormState) return;
    const form = field.closest("form");
    if (document.body.classList.contains("screen-query-mode") || form?.method?.toLowerCase() === "get" || field.closest("[data-disable-toolbar-actions='true']")) return;
    if (document.body.dataset.canSave !== "true" || form?.dataset.readonlyLock === "true") return;
    if (!await ensureCurrentRecordLock(form)) return;
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = false;
    setActionStatus("EDIÇÃO");
    form?.setAttribute("data-dirty", "true");
    persistCurrentFormState(form);
  });

  document.addEventListener("change", async function (event) {
    if (!event.target.closest("input, select, textarea")) return;
    if (!event.isTrusted && event.target.closest("[data-document-editor-form]")) return;
    if (event.target.matches("[data-state-select]")) {
      loadCitiesForState(event.target.value);
    }
    if (event.target.matches("[data-linked-state]")) {
      loadLinkedCities(event.target.dataset.linkedState, event.target.value);
    }
    if (event.target.matches("[data-linked-cep]")) {
      loadAddressForCep(event.target.dataset.linkedCep, event.target.value);
    }
    if (event.target.matches("[data-option-label-target]")) {
      syncLinkedOptionLabel(event.target);
    }
    if (event.target.matches("[data-cep-state-select]")) {
      filterCepCitiesForState(event.target);
    }
    if (isRestoringFormState) return;
    if (event.target.matches("[data-provider-type]")) {
      const councilField = document.querySelector("[data-provider-council]");
      let councilMap = {};
      try {
        councilMap = JSON.parse(event.target.dataset.councilMap || "{}");
      } catch (error) {
        councilMap = {};
      }
      const council = councilMap[event.target.value];
      if (councilField && council) {
        councilField.value = council;
        councilField.dispatchEvent(new Event("change", { bubbles: true }));
      } else if (event.target.value) {
        if (councilField) councilField.value = "";
        showBlockingNotification({
          title: "Conselho não vinculado",
          message: "Este tipo de prestador não possui conselho vinculado. O cadastro pode continuar normalmente.",
          confirmText: "Ignorar",
          cancelText: "Fechar",
          type: "info",
          initialFocus: "cancel",
        }).then((ignored) => {
          if (ignored) {
            focusNextField(event.target);
          } else {
            event.target.focus();
          }
        });
      }
      if (event.target.matches("[data-provider-permissions]")) {
        applyProviderPermissionSuggestions(event.target.value);
      }
    }
    if (event.target.matches("[data-user-provider]") && event.target.value) {
      fetch(`/accounts/usuarios/prestador/${encodeURIComponent(event.target.value)}/dados/`)
        .then((response) => response.json())
        .then((payload) => {
          Object.entries(payload).forEach(([fieldName, value]) => {
            const field = document.querySelector(`[name="${fieldName}"]`);
            if (!field || field.value || !value) return;
            if (field instanceof HTMLSelectElement && !Array.from(field.options).some((option) => option.value === value)) {
              field.add(new Option(value, value));
            }
            field.value = value;
            field.dispatchEvent(new Event("input", { bubbles: true }));
          });
        });
    }
    if (event.target.matches("[data-same-address]")) {
      copyResidentialAddressToCommercial(event.target.checked);
    }
    if (isRestoringFormState) return;
    const form = event.target.closest("form");
    if (document.body.classList.contains("screen-query-mode") || form?.method?.toLowerCase() === "get" || event.target.closest("[data-disable-toolbar-actions='true']")) return;
    if (document.body.dataset.canSave !== "true" || form?.dataset.readonlyLock === "true") return;
    if (!await ensureCurrentRecordLock(form)) return;
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = false;
    setActionStatus("EDIÇÃO");
    form?.setAttribute("data-dirty", "true");
    persistCurrentFormState(form);
  });

  async function loadCitiesForState(state) {
    const citySelect = document.querySelector("[data-city-select]");
    if (!citySelect) return;
    citySelect.innerHTML = '<option value=""></option>';
    if (!state) return;
    const response = await fetch(`/global/tabelas/auxiliares/cidades-opcoes/?uf=${encodeURIComponent(state)}`);
    const payload = await response.json();
    citySelect.innerHTML = '<option value=""></option>' + (payload.cidades || [])
      .map((city) => `<option value="${escapeHTML(city.value)}">${escapeHTML(city.label)}</option>`)
      .join("");
  }

  function isValidCPF(value) {
    const digits = onlyDigits(value);
    if (digits.length !== 11 || /^(\d)\1{10}$/.test(digits)) return false;
    const calculate = (size) => {
      let total = 0;
      for (let index = 0; index < size; index += 1) {
        total += Number(digits[index]) * (size + 1 - index);
      }
      return (total * 10 % 11) % 10;
    };
    return calculate(9) === Number(digits[9]) && calculate(10) === Number(digits[10]);
  }

  async function loadLinkedCities(group, state, selectedValue = "") {
    const citySelect = document.querySelector(`[data-linked-city="${CSS.escape(group)}"]`);
    if (!citySelect) return;
    citySelect.innerHTML = '<option value=""></option>';
    if (!state) return;
    const response = await fetch(`/global/tabelas/auxiliares/cidades-opcoes/?uf=${encodeURIComponent(state)}`);
    const payload = await response.json();
    citySelect.innerHTML = '<option value=""></option>' + (payload.cidades || [])
      .map((city) => `<option value="${escapeHTML(city.value)}">${escapeHTML(city.label)}</option>`)
      .join("");
    citySelect.value = selectedValue;
  }

  async function loadAddressForCep(group, cep) {
    if (!cep) return;
    const response = await fetch(`/global/tabelas/auxiliares/cep-opcao/?cep=${encodeURIComponent(cep)}`);
    const payload = await response.json();
    if (!payload.estado) {
      const shouldOpen = await showBlockingNotification({
        title: "CEP não cadastrado",
        message: "O CEP informado não existe no cadastro global. Deseja abrir a tela de CEPs?",
        confirmText: "Abrir CEPs",
        cancelText: "Continuar manualmente",
        type: "info",
      });
      if (shouldOpen) window.location.href = "/global/ceps/";
      return;
    }
    const stateSelect = document.querySelector(`[data-linked-state="${CSS.escape(group)}"]`);
    if (stateSelect) {
      stateSelect.value = payload.estado;
      await loadLinkedCities(group, payload.estado, payload.cidade || "");
    }
    const suffix = group === "comercial" ?"_comercial" : "";
    const addressFields = {
      [`tp_logradouro${suffix}`]: payload.tipo_logradouro,
      [`ds_endereco${suffix}`]: payload.logradouro,
      [`ds_bairro${suffix}`]: payload.bairro,
    };
    Object.entries(addressFields).forEach(([fieldName, value]) => {
      const field = document.querySelector(`[name="${fieldName}"]`);
      if (!field || !value) return;
      if (field instanceof HTMLSelectElement && !Array.from(field.options).some((option) => option.value === value)) {
        field.add(new Option(value, value));
      }
      field.value = value;
      field.dispatchEvent(new Event("change", { bubbles: true }));
    });
  }

  function validateStructuredField(field, notify = false) {
    if (!field?.value?.trim()) {
      field?.classList.remove("field-invalid");
      field.setCustomValidity?.("");
      return true;
    }
    let message = "";
    if (field.matches("[data-validate-cpf]") && !isValidCPF(field.value)) {
      message = "Informe um CPF válido.";
    } else if (field.matches("[data-validate-email]") && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(field.value)) {
      message = "Informe um e-mail válido.";
    } else if (field.matches("[data-validate-cnes]") && !/^\d{7}$/.test(onlyDigits(field.value))) {
      message = "O CNES deve conter exatamente 7 dígitos.";
    }
    field.classList.toggle("field-invalid", Boolean(message));
    field.setCustomValidity(message);
    if (message && notify) {
      showBlockingNotification({
        title: "Valor inválido",
        message,
        confirmText: "OK",
        type: "error",
        focusTarget: field,
      });
    }
    return !message;
  }

  document.addEventListener("blur", async function (event) {
    const structuredField = event.target.closest("[data-validate-cpf], [data-validate-email], [data-validate-cnes]");
    if (structuredField && !validateStructuredField(structuredField, true)) return;
    const field = event.target.closest("[data-unique-patient]");
    if (!field || !field.value.trim()) return;
    const currentValue = field.value.trim();
    if (field.dataset.duplicateCheckedValue === currentValue) return;
    const form = field.closest("form");
    const params = new URLSearchParams({
      field: field.dataset.uniquePatient,
      value: currentValue,
      paciente: form?.dataset.patientId || "",
    });
    const response = await fetch(`/atendimento/pacientes/verificar-unico/?${params.toString()}`);
    const payload = await response.json();
    field.dataset.duplicateCheckedValue = currentValue;
    if (!payload.exists) {
      field.classList.remove("field-duplicate");
      field.setCustomValidity("");
      return;
    }
    field.classList.add("field-duplicate");
    field.setCustomValidity(payload.message || "Dado já cadastrado.");
    await showBlockingNotification({
      title: "Registro já cadastrado",
      message: payload.message || "Dado já cadastrado para outro paciente.",
      confirmText: "OK",
      store: true,
      type: "error",
      focusTarget: field,
    });
  }, true);

  document.addEventListener("input", function (event) {
    const field = event.target.closest("[data-unique-patient]");
    const structuredField = event.target.closest("[data-validate-cpf], [data-validate-email], [data-validate-cnes]");
    if (structuredField) validateStructuredField(structuredField);
    if (!field) return;
    field.classList.remove("field-duplicate");
    field.setCustomValidity("");
    field.dataset.duplicateCheckedValue = "";
  });

  function onlyDigits(value) {
    return String(value || "").replace(/\D/g, "");
  }

  function formatCPF(value) {
    const digits = onlyDigits(value).slice(0, 11);
    return digits
      .replace(/^(\d{3})(\d)/, "$1.$2")
      .replace(/^(\d{3})\.(\d{3})(\d)/, "$1.$2.$3")
      .replace(/^(\d{3})\.(\d{3})\.(\d{3})(\d{1,2})/, "$1.$2.$3-$4");
  }

  function formatCellphone(value) {
    const digits = onlyDigits(value).slice(0, 11);
    if (digits.length <= 2) return digits.replace(/^(\d{0,2})/, "($1");
    if (digits.length <= 7) return digits.replace(/^(\d{2})(\d{0,1})(\d{0,4})/, "($1) $2 $3").trim();
    return digits.replace(/^(\d{2})(\d{1})(\d{4})(\d{0,4})/, "($1) $2 $3-$4").trim();
  }

  function setupSpecialtyManager() {
    const manager = document.querySelector("[data-specialty-manager]");
    if (!manager) return;
    const storage = manager.querySelector("[data-specialty-values]");
    const picker = manager.querySelector("[data-specialty-picker]");
    const chips = manager.querySelector("[data-specialty-chips]");
    const addButton = manager.querySelector("[data-specialty-add]");
    const openButton = manager.querySelector("[data-specialty-open]");
    const addRow = manager.querySelector("[data-specialty-add-row]");
    const primary = document.querySelector("[data-primary-specialty]");
    if (!storage || !picker || !chips || !openButton || !addRow) return;

    const options = Array.from(storage.options).map((option) => ({
      value: option.value,
      label: option.textContent.trim(),
    })).filter((option) => option.value);

    const selectedValues = () => Array.from(storage.selectedOptions).map((option) => option.value);

    const render = () => {
      const selected = new Set(selectedValues());
      chips.innerHTML = options
        .filter((option) => selected.has(option.value))
        .map((option) => (
          `<span class="specialty-chip">${escapeHTML(option.label)}`
          + `<button type="button" data-specialty-remove="${escapeHTML(option.value)}" aria-label="Remover ${escapeHTML(option.label)}">&times;</button></span>`
        ))
        .join("");
      if (!chips.children.length) {
        chips.innerHTML = '<span class="specialty-empty">Nenhuma especialidade adicionada.</span>';
      }

      const pickerValue = picker.value;
      picker.innerHTML = '<option value="">Adicionar especialidade...</option>' + options
        .filter((option) => !selected.has(option.value))
        .map((option) => `<option value="${escapeHTML(option.value)}">${escapeHTML(option.label)}</option>`)
        .join("");
      picker.value = Array.from(picker.options).some((option) => option.value === pickerValue) ?pickerValue : "";

      if (primary) {
        const currentPrimary = primary.value;
        const primaryOptions = document.body.classList.contains("screen-query-mode")
          ? options
          : options.filter((option) => selected.has(option.value));
        primary.innerHTML = '<option value=""></option>' + primaryOptions
          .map((option) => `<option value="${escapeHTML(option.value)}">${escapeHTML(option.label)}</option>`)
          .join("");
        const hasCurrentPrimary = primaryOptions.some((option) => option.value === currentPrimary);
        primary.value = hasCurrentPrimary ? currentPrimary : (
          document.body.classList.contains("screen-query-mode") ? "" : (selectedValues()[0] || "")
        );
      }
    };

    const addSelected = () => {
      if (!picker.value) return;
      const option = Array.from(storage.options).find((item) => item.value === picker.value);
      if (option) {
        option.selected = true;
        storage.dispatchEvent(new Event("change", { bubbles: true }));
      }
      render();
      addRow.hidden = false;
      openButton.hidden = true;
      picker.focus();
    };

    const resetInterface = () => {
      picker.value = "";
      addRow.hidden = true;
      openButton.hidden = false;
      render();
    };

    openButton.addEventListener("click", () => {
      if (!options.length) {
        addNotificationToHistory(
          manager.dataset.emptyOptionsMessage || "Lista sem valores cadastrados para seleção.",
          "warning",
          false
        );
        return;
      }
      openButton.hidden = true;
      addRow.hidden = false;
      picker.focus();
    });
    addButton?.addEventListener("click", addSelected);
    picker.addEventListener("change", addSelected);
    picker.addEventListener("keydown", (event) => {
      if (event.key !== "Enter") return;
      event.preventDefault();
      addSelected();
    });
    storage.addEventListener("change", render);
    document.addEventListener("celeris:query-mode-change", render);
    manager.closest("form")?.addEventListener("celeris:reset-multiselects", resetInterface);
    chips.addEventListener("click", (event) => {
      const removeButton = event.target.closest("[data-specialty-remove]");
      if (!removeButton) return;
      const option = Array.from(storage.options).find((item) => item.value === removeButton.dataset.specialtyRemove);
      if (option) {
        option.selected = false;
        storage.dispatchEvent(new Event("change", { bubbles: true }));
      }
      render();
    });
    render();
  }

  function setupAssignmentManagers() {
    document.querySelectorAll("[data-assignment-manager]").forEach((manager) => {
      const storage = manager.querySelector("[data-assignment-values]");
      const picker = manager.querySelector("[data-assignment-picker]");
      const chips = manager.querySelector("[data-assignment-chips]");
      const addButton = manager.querySelector("[data-assignment-add]");
      const openButton = manager.querySelector("[data-assignment-open]");
      const addRow = manager.querySelector("[data-assignment-add-row]");
      const primaryProviderType = manager.matches("[data-provider-type-assignment]")
        ? document.querySelector("[data-provider-type]")
        : null;
      if (!storage || !picker || !chips || !openButton || !addRow) return;
      const options = Array.from(storage.options)
        .filter((option) => option.value)
        .map((option) => ({ value: option.value, label: option.textContent.trim() }));
      const selectedValues = () => Array.from(storage.selectedOptions).map((option) => option.value);

      const render = () => {
        const selected = new Set(selectedValues());
        chips.innerHTML = options
          .filter((option) => selected.has(option.value))
          .map((option) => (
            `<span class="specialty-chip">${escapeHTML(option.label)}`
            + `<button type="button" data-assignment-remove="${escapeHTML(option.value)}" aria-label="Remover ${escapeHTML(option.label)}">&times;</button></span>`
          ))
          .join("");
        if (!chips.children.length) {
          chips.innerHTML = `<span class="specialty-empty">${escapeHTML(manager.dataset.assignmentEmpty || "Nenhum item atribuído.")}</span>`;
        }
        picker.innerHTML = '<option value="">Selecionar...</option>' + options
          .filter((option) => !selected.has(option.value))
          .map((option) => `<option value="${escapeHTML(option.value)}">${escapeHTML(option.label)}</option>`)
          .join("");
        if (primaryProviderType) {
          const currentPrimary = primaryProviderType.value;
          const queryMode = document.body.classList.contains("screen-query-mode");
          const primaryOptions = queryMode ? options : options.filter((option) => selected.has(option.value));
          primaryProviderType.innerHTML = '<option value=""></option>' + primaryOptions
            .map((option) => `<option value="${escapeHTML(option.value)}">${escapeHTML(option.label)}</option>`)
            .join("");
          const nextPrimary = primaryOptions.some((option) => option.value === currentPrimary)
            ? currentPrimary
            : (queryMode ? "" : (selectedValues()[0] || ""));
          primaryProviderType.value = nextPrimary;
          if (!queryMode && nextPrimary !== currentPrimary) {
            primaryProviderType.dispatchEvent(new Event("change", { bubbles: true }));
          }
        }
      };

      const addSelected = () => {
        const option = Array.from(storage.options).find((item) => item.value === picker.value);
        if (!option) return;
        option.selected = true;
        storage.dispatchEvent(new Event("change", { bubbles: true }));
        render();
        picker.focus();
      };

      const resetInterface = () => {
        picker.value = "";
        addRow.hidden = true;
        openButton.hidden = false;
        render();
      };

      openButton.addEventListener("click", () => {
        if (!options.length) {
          addNotificationToHistory(
            manager.dataset.emptyOptionsMessage || "Lista sem valores cadastrados para seleção.",
            "warning",
            false
          );
          return;
        }
        openButton.hidden = true;
        addRow.hidden = false;
        picker.focus();
      });
      addButton?.addEventListener("click", addSelected);
      picker.addEventListener("change", addSelected);
      picker.addEventListener("keydown", (event) => {
        if (event.key !== "Enter") return;
        event.preventDefault();
        addSelected();
      });
      storage.addEventListener("change", render);
      document.addEventListener("celeris:query-mode-change", render);
      manager.closest("form")?.addEventListener("celeris:reset-multiselects", resetInterface);
      chips.addEventListener("click", (event) => {
        const removeButton = event.target.closest("[data-assignment-remove]");
        if (!removeButton) return;
        const option = Array.from(storage.options).find(
          (item) => item.value === removeButton.dataset.assignmentRemove
        );
        if (option) {
          option.selected = false;
          storage.dispatchEvent(new Event("change", { bubbles: true }));
        }
        render();
      });
      render();
    });
  }

  function setupRoleModuleVisibility() {
    const moduleFields = document.querySelectorAll("[data-role-module]");
    if (!moduleFields.length) return;
    const update = () => {
      moduleFields.forEach((field) => {
        const section = document.querySelector(`[data-role-screen-module="${field.dataset.roleModule}"]`);
        if (!section) return;
        section.hidden = !field.checked;
        if (!field.checked) {
          section.querySelectorAll('input[type="checkbox"]').forEach((checkbox) => {
            checkbox.checked = false;
          });
        }
      });
    };
    moduleFields.forEach((field) => field.addEventListener("change", update));
    update();
  }

  function setupStandardCheckboxes() {
    document.querySelectorAll('form input[type="checkbox"]').forEach((checkbox) => {
      checkbox.closest("label")?.classList.add("provider-checkbox");
    });
  }

  function setupFormSectionAccordion() {
    document.querySelectorAll(".provider-form, .patient-form, .user-form, .role-form, .ticket-config-form").forEach((form) => {
      const sections = Array.from(form.querySelectorAll(":scope > details.form-section"));
      if (!sections.length) return;
      let activePanelHost = form.querySelector(":scope > .form-section-active-panel");
      if (!activePanelHost) {
        activePanelHost = document.createElement("div");
        activePanelHost.className = "form-section-active-panel";
        form.appendChild(activePanelHost);
      }
      sections.forEach((section) => {
        let panel = section.querySelector(":scope > .form-section-panel");
        if (!panel) {
          panel = document.createElement("div");
          panel.className = "form-section-panel";
          Array.from(section.childNodes).forEach((node) => {
            if (node.nodeType === Node.ELEMENT_NODE && node.matches("summary")) return;
            panel.appendChild(node);
          });
          section.appendChild(panel);
        }
        section.celerisSectionPanel = panel;
      });
      form.style.setProperty("--form-section-count", String(Math.max(sections.length, 1)));
      const activateSectionPanel = (section) => {
        const panel = section.celerisSectionPanel || section.querySelector(":scope > .form-section-panel");
        if (!panel) return;
        sections.forEach((item) => {
          const itemPanel = item.celerisSectionPanel || item.querySelector(":scope > .form-section-panel");
          if (!itemPanel || item === section || itemPanel.parentElement === item) return;
          item.appendChild(itemPanel);
        });
        activePanelHost.replaceChildren(panel);
      };
      const anchoredSection = window.location.hash
        ? sections.find((section) => section.id && `#${section.id}` === window.location.hash)
        : null;
      const initiallyOpenSection = anchoredSection || sections.find((section) => section.open) || sections[0];
      sections.forEach((section) => {
        section.open = section === initiallyOpenSection;
      });
      activateSectionPanel(initiallyOpenSection);
      if (anchoredSection) {
        window.requestAnimationFrame(() => anchoredSection.scrollIntoView({ block: "start" }));
      }
      sections.forEach((section) => {
        section.addEventListener("celeris:activate-section", () => {
          activateSectionPanel(section);
          sections.forEach((otherSection) => {
            if (otherSection !== section) otherSection.open = false;
          });
        });
        section.addEventListener("toggle", () => {
          if (!section.open) return;
          activateSectionPanel(section);
          sections.forEach((otherSection) => {
            if (otherSection !== section) otherSection.open = false;
          });
        });
      });

      const editableFields = (section) => Array.from(
        section.celerisSectionPanel?.querySelectorAll(
          "input:not([type='hidden']):not([disabled]):not([readonly]), select:not([disabled]), textarea:not([disabled]):not([readonly])"
        ) || []
      ).filter((field) => field.offsetParent !== null);
      const focusSection = (section, fromEnd = false) => {
        if (!section) return;
        section.open = true;
        activateSectionPanel(section);
        sections.forEach((otherSection) => {
          if (otherSection !== section) otherSection.open = false;
        });
        window.requestAnimationFrame(() => window.requestAnimationFrame(() => {
          const fields = editableFields(section);
          const target = fromEnd ? fields.at(-1) : fields[0];
          target?.focus({ preventScroll: true });
          target?.scrollIntoView({ block: "nearest", inline: "nearest" });
        }));
      };
      form.addEventListener("keydown", (event) => {
        const activeSection = sections.find((section) => section.open);
        if (!activeSection || !event.target.matches("input, select, textarea")) return;
        const fields = editableFields(activeSection);
        if (!fields.length) return;
        const fieldIndex = fields.indexOf(event.target);
        const sectionIndex = sections.indexOf(activeSection);
        const isForward = (event.key === "Tab" && !event.shiftKey && !event.ctrlKey)
          || (event.key === "Enter" && !event.shiftKey && !event.ctrlKey && !event.target.matches("textarea"));
        const isBackward = event.key === "Tab" && (event.shiftKey || event.ctrlKey);
        if (isForward && fieldIndex === fields.length - 1 && sectionIndex < sections.length - 1) {
          event.preventDefault();
          focusSection(sections[sectionIndex + 1]);
        } else if (isBackward && fieldIndex === 0 && sectionIndex > 0) {
          event.preventDefault();
          focusSection(sections[sectionIndex - 1], true);
        }
      });
    });
  }

  function setupScaleProviderSpecialties() {
    document.querySelectorAll(".scale-form").forEach((form) => {
      const provider = form.querySelector("[data-provider-specialties]");
      const specialty = form.querySelector("[data-provider-specialty-target]");
      if (!provider || !specialty) return;
      let byProvider = {};
      let allSpecialties = [];
      try {
        byProvider = JSON.parse(provider.dataset.providerSpecialties || "{}");
        allSpecialties = JSON.parse(specialty.dataset.allSpecialties || "[]");
      } catch (error) {
        byProvider = {};
        allSpecialties = [];
      }
      const synchronize = () => {
        const currentValue = specialty.value;
        const queryMode = document.body.classList.contains("screen-query-mode");
        const available = queryMode ? allSpecialties : (byProvider[provider.value] || []);
        specialty.replaceChildren(new Option("", ""));
        available.forEach((item) => specialty.add(new Option(item.label, item.value)));
        specialty.value = available.some((item) => String(item.value) === currentValue) ? currentValue : "";
      };
      provider.addEventListener("change", synchronize);
      document.addEventListener("celeris:query-mode-change", synchronize);
      synchronize();
    });
  }

  function setupNavigationBuilder() {
    const builder = document.querySelector(".navigation-builder");
    const form = document.querySelector("[data-navigation-reorder-form]");
    if (!builder || !form) return;
    let draggedItem = null;
    const serializeOrder = () => {
      const structure = {};
      builder.querySelectorAll("[data-navigation-parent]").forEach((container) => {
        const parent = container.dataset.navigationParent || "";
        structure[parent] = Array.from(
          container.querySelectorAll(":scope > [data-navigation-item]"),
          (item) => item.dataset.navigationItem || "",
        ).filter(Boolean);
      });
      return JSON.stringify(structure);
    };

    builder.addEventListener("dragstart", (event) => {
      const handle = event.target.closest("[data-navigation-node]");
      if (!handle || event.target.closest("a, button")) return;
      draggedItem = handle.closest("[data-navigation-item]");
      if (!draggedItem) return;
      draggedItem.classList.add("is-dragging");
      event.dataTransfer.effectAllowed = "move";
      event.dataTransfer.setData("text/plain", draggedItem.dataset.navigationItem || "");
    });

    builder.addEventListener("dragover", (event) => {
      if (!draggedItem) return;
      const targetItem = event.target.closest("[data-navigation-item]");
      const sourceContainer = draggedItem.parentElement;
      if (!targetItem || targetItem === draggedItem || targetItem.parentElement !== sourceContainer) return;
      event.preventDefault();
      const targetRect = targetItem.getBoundingClientRect();
      sourceContainer.insertBefore(draggedItem, event.clientY < targetRect.top + targetRect.height / 2 ? targetItem : targetItem.nextSibling);
    });

    builder.addEventListener("drop", async (event) => {
      if (!draggedItem) return;
      event.preventDefault();
      const container = draggedItem.parentElement;
      const payload = new FormData(form);
      payload.append("node", draggedItem.dataset.navigationItem || "");
      payload.append("parent", container?.dataset.navigationParent || "");
      container?.querySelectorAll(":scope > [data-navigation-item]").forEach((item) => payload.append("order", item.dataset.navigationItem || ""));
      try {
        const response = await fetch(form.action, {method: "POST", credentials: "same-origin", body: payload});
        if (!response.ok) throw new Error("Não foi possível salvar a ordem.");
        const dirtyField = document.querySelector("[data-navigation-order-dirty]");
        if (dirtyField) {
          dirtyField.value = serializeOrder();
          dirtyField.dispatchEvent(new Event("input", {bubbles: true}));
          dirtyField.dispatchEvent(new Event("change", {bubbles: true}));
        }
        const saveButton = document.querySelector('[data-action="save"]');
        if (saveButton) saveButton.disabled = false;
        addNotificationToHistory("Ordem do menu atualizada.", "success", false);
      } catch (error) {
        addNotificationToHistory(error.message || "Não foi possível salvar a ordem.", "error", false);
        window.location.reload();
      }
    });

    builder.addEventListener("dragend", () => {
      draggedItem?.classList.remove("is-dragging");
      draggedItem = null;
    });
  }

  function setupCallIconTables() {
    const sanitizeSvg = (value) => {
      const parsed = new DOMParser().parseFromString(value || "", "image/svg+xml");
      const svg = parsed.documentElement;
      if (!svg || svg.nodeName.toLowerCase() !== "svg" || parsed.querySelector("parsererror")) return "";
      const allowedTags = new Set(["svg", "g", "path", "circle", "ellipse", "rect", "line", "polyline", "polygon", "title", "desc"]);
      const allowedAttributes = new Set([
        "xmlns", "viewbox", "preserveaspectratio", "role", "aria-hidden", "focusable", "class",
        "width", "height", "fill", "fill-opacity", "fill-rule", "stroke", "stroke-opacity",
        "d", "x", "y", "x1", "x2", "y1", "y2", "cx", "cy", "r", "rx", "ry", "points",
        "stroke-width", "stroke-linecap", "stroke-linejoin", "stroke-dasharray", "stroke-dashoffset",
        "stroke-miterlimit", "clip-rule", "opacity", "transform", "vector-effect",
      ]);
      Array.from(svg.querySelectorAll("*")).forEach((element) => {
        if (!allowedTags.has(element.nodeName.toLowerCase())) {
          element.remove();
          return;
        }
        Array.from(element.attributes).forEach((attribute) => {
          if (!allowedAttributes.has(attribute.name.toLowerCase())) element.removeAttribute(attribute.name);
        });
      });
      Array.from(svg.attributes).forEach((attribute) => {
        if (!allowedAttributes.has(attribute.name.toLowerCase())) svg.removeAttribute(attribute.name);
      });
      return new XMLSerializer().serializeToString(svg);
    };
    const updatePreview = (source) => {
      const row = source.closest("[data-editable-row]") || source.closest(".call-icon-picker");
      const preview = row?.querySelector("[data-svg-preview], [data-icon-preview]");
      if (!preview) return;
      if (source.matches("[data-call-icon-select]")) {
        preview.innerHTML = sanitizeSvg(source.selectedOptions[0]?.dataset.svg || "");
        return;
      }
      preview.innerHTML = sanitizeSvg(source.value || "");
    };
    document.querySelectorAll("[data-svg-source], [data-call-icon-select]").forEach((source) => {
      source.addEventListener("input", () => updatePreview(source));
      source.addEventListener("change", () => updatePreview(source));
    });
    document.addEventListener("input", (event) => {
      if (event.target?.matches?.("[data-svg-source]")) updatePreview(event.target);
    });
    document.addEventListener("change", (event) => {
      if (event.target?.matches?.("[data-call-icon-select]")) updatePreview(event.target);
    });
  }

  function setupSystemIconPickers() {
    document.querySelectorAll("[data-system-icon-select]").forEach((select) => {
      const preview = select.closest(".system-icon-picker")?.querySelector("[data-system-icon-preview]");
      if (!preview) return;
      const updatePreview = () => {
        const iconKey = select.selectedOptions[0]?.dataset.iconKey || select.value;
        preview.innerHTML = iconKey ?iconMarkup(iconKey) : "";
        preview.classList.toggle("is-empty", !iconKey);
      };
      select.addEventListener("change", updatePreview);
      updatePreview();
    });
  }

  function setupSortableTables() {
    const currentOrdering = new URLSearchParams(window.location.search).get("ordem") || "";
    const renderIndicator = (element, fieldName) => {
      element.querySelector(".sort-indicator")?.remove();
      if (currentOrdering !== fieldName && currentOrdering !== `-${fieldName}`) return;
      const indicator = document.createElement("span");
      indicator.className = "sort-indicator";
      indicator.textContent = currentOrdering.startsWith("-") ?"▼" : "▲";
      element.appendChild(indicator);
    };

    document.querySelectorAll("table th a").forEach((link) => {
      const ordering = new URL(link.href, window.location.origin).searchParams.get("ordem") || "";
      const fieldName = ordering.replace(/^-/, "");
      if (fieldName) renderIndicator(link, fieldName);
      link.addEventListener("click", (event) => {
        event.preventDefault();
        const url = new URL(window.location.href);
        url.searchParams.set("ordem", ordering);
        url.searchParams.delete("pagina");
        storeCurrentListPosition();
        window.location.assign(url.toString());
      });
    });
    document.querySelectorAll("table th[data-sort-field]").forEach((header) => {
      const fieldName = header.dataset.sortField;
      header.classList.add("sortable-column");
      header.tabIndex = 0;
      renderIndicator(header, fieldName);
      const applyOrdering = () => {
        const url = new URL(window.location.href);
        url.searchParams.set("ordem", currentOrdering === fieldName ?`-${fieldName}` : fieldName);
        storeCurrentListPosition();
        window.location.href = url.toString();
      };
      header.addEventListener("click", applyOrdering);
      header.addEventListener("keydown", (event) => {
        if (event.key !== "Enter" && event.key !== " ") return;
        event.preventDefault();
        applyOrdering();
      });
    });
    document.querySelectorAll("table").forEach((table) => {
      const headers = Array.from(table.querySelectorAll("thead th"));
      headers.forEach((header, columnIndex) => {
        if (
          header.matches("[data-sort-field]")
          || header.querySelector("a")
          || /^(ação|ações)$/i.test(header.textContent.trim())
        ) return;
        header.classList.add("sortable-column");
        header.tabIndex = 0;
        const valueFor = (row) => {
          const cell = row.cells[columnIndex];
          const control = cell?.querySelector("input:not([type='hidden']), select, textarea");
          const raw = String(control?.value || cell?.textContent || "").trim();
          const dateMatch = raw.match(/^(\d{2})\/(\d{2})\/(\d{4})(?:\s+(\d{2}):(\d{2}))?/);
          if (dateMatch) {
            return new Date(
              Number(dateMatch[3]),
              Number(dateMatch[2]) - 1,
              Number(dateMatch[1]),
              Number(dateMatch[4] || 0),
              Number(dateMatch[5] || 0),
            ).getTime();
          }
          const numeric = Number(raw.replace(/\./g, "").replace(",", "."));
          return raw && Number.isFinite(numeric) ?numeric : raw.toLocaleLowerCase("pt-BR");
        };
        const applyClientOrdering = () => {
          const tbody = table.tBodies[0];
          if (!tbody) return;
          const groups = [];
          Array.from(tbody.rows).forEach((row) => {
            if (row.classList.contains("agenda-slot-details") && groups.length) {
              groups[groups.length - 1].push(row);
            } else {
              groups.push([row]);
            }
          });
          const descending = header.dataset.clientSortDirection === "asc";
          headers.forEach((item) => {
            item.querySelector(".sort-indicator")?.remove();
            delete item.dataset.clientSortDirection;
          });
          header.dataset.clientSortDirection = descending ?"desc" : "asc";
          groups.sort((left, right) => {
            const leftValue = valueFor(left[0]);
            const rightValue = valueFor(right[0]);
            const comparison = typeof leftValue === "number" && typeof rightValue === "number"
              ?leftValue - rightValue
              : String(leftValue).localeCompare(String(rightValue), "pt-BR", { numeric: true, sensitivity: "base" });
            return descending ?-comparison : comparison;
          });
          const indicator = document.createElement("span");
          indicator.className = "sort-indicator";
          indicator.textContent = descending ?"▼" : "▲";
          header.appendChild(indicator);
          groups.flat().forEach((row) => tbody.appendChild(row));
        };
        header.addEventListener("click", applyClientOrdering);
        header.addEventListener("keydown", (event) => {
          if (event.key !== "Enter" && event.key !== " ") return;
          event.preventDefault();
          applyClientOrdering();
        });
      });
    });
  }

  function setupResizableTables() {
    document.querySelectorAll("table").forEach((table) => {
      const headers = Array.from(table.querySelectorAll("thead th"));
      let colgroup = table.querySelector("colgroup[data-resizable-columns]");
      if (!colgroup) {
        colgroup = document.createElement("colgroup");
        colgroup.dataset.resizableColumns = "true";
        headers.forEach(() => colgroup.appendChild(document.createElement("col")));
        table.prepend(colgroup);
      }
      headers.forEach((header, index) => {
        if (index >= headers.length - 1) return;
        if (header.querySelector(".column-resize-handle")) return;
        header.style.position = "sticky";
        const handle = document.createElement("span");
        handle.className = "column-resize-handle";
        handle.dataset.columnResize = String(index);
        handle.addEventListener("click", (event) => {
          event.preventDefault();
          event.stopPropagation();
        });
        handle.addEventListener("pointerdown", (event) => {
          event.preventDefault();
          event.stopPropagation();
          const startX = event.clientX;
          const widths = headers.map((item) => item.getBoundingClientRect().width);
          const startWidth = widths[index];
          const col = colgroup.children[index];
          widths.forEach((width, columnIndex) => {
            const currentCol = colgroup.children[columnIndex];
            if (!currentCol) return;
            currentCol.style.width = `${width}px`;
            currentCol.style.minWidth = `${width}px`;
          });
          table.style.width = `${widths.reduce((total, width) => total + width, 0)}px`;
          table.style.minWidth = table.style.width;
          handle.setPointerCapture?.(event.pointerId);
          document.body.classList.add("column-resizing");
          const resize = (moveEvent) => {
            const nextWidth = Math.max(64, startWidth + moveEvent.clientX - startX);
            if (col) {
              col.style.width = `${nextWidth}px`;
              col.style.minWidth = `${nextWidth}px`;
              table.style.width = `${widths.reduce((total, width, columnIndex) => (
                total + (columnIndex === index ?nextWidth : width)
              ), 0)}px`;
              table.style.minWidth = table.style.width;
            }
          };
          const stop = () => {
            document.body.classList.remove("column-resizing");
            handle.removeEventListener("pointermove", resize);
            handle.removeEventListener("pointerup", stop);
            handle.removeEventListener("pointercancel", stop);
          };
          handle.addEventListener("pointermove", resize);
          handle.addEventListener("pointerup", stop);
          handle.addEventListener("pointercancel", stop);
        });
        header.appendChild(handle);
      });
    });
  }

  function syncLinkedOptionLabel(field) {
    const targetName = field.dataset.optionLabelTarget;
    if (!targetName) return;
    const form = field.closest("form");
    const target = form?.querySelector(`[name="${CSS.escape(targetName)}"]`);
    if (target) target.value = field.selectedOptions?.[0]?.textContent?.trim() || "";
  }

  function filterCepCitiesForState(stateField) {
    const targetName = stateField.dataset.cityTarget;
    if (!targetName) return;
    const form = stateField.closest("form") || document;
    const citySelect = form.querySelector(`[name="${CSS.escape(targetName)}"]`);
    if (!citySelect) return;
    const state = stateField.value;
    Array.from(citySelect.options).forEach((option) => {
      const visible = !option.value || (state && option.dataset.state === state);
      option.hidden = !visible;
      option.disabled = !visible;
    });
    const selectedOption = citySelect.selectedOptions[0];
    if (selectedOption?.disabled) {
      citySelect.value = "";
      syncLinkedOptionLabel(citySelect);
    }
  }

  function setupCepCityDependencies() {
    document.querySelectorAll("[data-cep-state-select]").forEach(filterCepCitiesForState);
  }

  function copyResidentialAddressToCommercial(lockFields) {
    const fieldMap = {
      cd_cep: "cd_cep_comercial",
      sg_estado: "sg_estado_comercial",
      ds_cidade: "ds_cidade_comercial",
      tp_logradouro: "tp_logradouro_comercial",
      ds_endereco: "ds_endereco_comercial",
      nr_endereco: "nr_endereco_comercial",
      ds_complemento: "ds_complemento_comercial",
      ds_bairro: "ds_bairro_comercial",
    };
    Object.entries(fieldMap).forEach(([sourceName, targetName]) => {
      const source = document.querySelector(`[name="${sourceName}"]`);
      const target = document.querySelector(`[name="${targetName}"]`);
      if (!target) return;
      if (lockFields && source) {
        if (target.tagName === "SELECT" && !Array.from(target.options).some((option) => option.value === source.value)) {
          target.add(new Option(source.selectedOptions?.[0]?.textContent || source.value, source.value));
        }
        target.value = source.value;
      }
      target.disabled = Boolean(lockFields);
    });
  }

  function applyProviderPermissionSuggestions(providerType) {
    const suggestions = {
      MEDICO: ["sn_permite_agenda", "sn_permite_atendimento", "sn_permite_prescricao"],
      ENFERMEIRO: ["sn_permite_agenda", "sn_permite_atendimento", "sn_permite_classificacao"],
      TECNICO_ENFERMAGEM: ["sn_permite_classificacao"],
    };
    const permissionFields = [
      "sn_permite_agenda",
      "sn_permite_atendimento",
      "sn_permite_prescricao",
      "sn_permite_classificacao",
    ];
    if (!providerType || !suggestions[providerType]) return;
    permissionFields.forEach((fieldName) => {
      const field = document.querySelector(`[name="${fieldName}"]`);
      if (field) field.checked = suggestions[providerType].includes(fieldName);
    });
  }

  function setupActionButtons() {
    const queryButton = document.querySelector("[data-query-toggle]");
    const newButton = document.querySelector('[data-action="new"]');
    const continueButton = document.querySelector('[data-action="continue"]');
    const clearButton = document.querySelector('[data-action="clear"]');
    const removeButton = document.querySelector('[data-action="remove"]');
    const previousButton = document.querySelector('[data-action="previous"]');
    const nextButton = document.querySelector('[data-action="next"]');
    const firstButton = document.querySelector('[data-action="first"]');
    const lastButton = document.querySelector('[data-action="last"]');
    const closeButton = document.querySelector('[data-action="close"]');
    const saveButton = document.querySelector('[data-action="save"]');
    const reloadButton = document.querySelector('[data-action="reload"]');
    const printButton = document.querySelector('[data-action="print"]');
    const cancelQueryIcon = document.querySelector('[data-query-cancel] [data-nav-icon]');
    const tableForm = getEditableTableForm();
    const contextualRemoveTarget = document.querySelector("[data-toolbar-remove-target].selected");
    const hasContextualRemoveTargets = Boolean(document.querySelector("[data-toolbar-remove-target]"));
    const isHome = document.body.dataset.tabUrl === "/";
    const isQueryMode = document.body.classList.contains("screen-query-mode");

    if (document.querySelector("[data-disable-toolbar-actions='true']")) {
      document.querySelectorAll(".toolbar-actions .toolbar-button").forEach((button) => {
        const isClose = button.matches('[data-action="close"]');
        button.hidden = !isClose;
        button.disabled = !isClose;
      });
      return;
    }

    const subscreenToolbar = document.querySelector("[data-subscreen-toolbar='true']");
    if (subscreenToolbar) {
      const allowContinue = subscreenToolbar.dataset.subscreenAllowContinue === "true";
      document.querySelectorAll(".toolbar-actions .toolbar-button").forEach((button) => {
        const isAllowed = button.matches('[data-action="save"], [data-action="close"]')
          || (allowContinue && button.matches('[data-action="continue"]'));
        button.hidden = !isAllowed;
        if (!isAllowed) button.disabled = true;
      });
      if (saveButton) {
        saveButton.hidden = document.body.dataset.canSave !== "true";
      }
      if (continueButton) {
        continueButton.hidden = !allowContinue || !document.body.dataset.continueUrl;
        continueButton.disabled = !allowContinue || !document.body.dataset.continueUrl;
      }
      if (closeButton) closeButton.disabled = false;
      return;
    }

    if (isHome) {
      [queryButton, clearButton, newButton, continueButton, removeButton, firstButton, previousButton, nextButton, lastButton, closeButton].forEach((button) => {
        if (button) button.disabled = true;
      });
      return;
    }

    if (queryButton) {
      queryButton.hidden = document.body.dataset.canQuery !== "true";
      queryButton.disabled = document.body.dataset.canQuery !== "true";
    }
    if (isQueryMode) {
      [saveButton, newButton, continueButton, removeButton].forEach((button) => {
        if (button) button.disabled = true;
      });
    }
    if (saveButton && document.body.dataset.canSave !== "true") {
      saveButton.hidden = true;
      saveButton.disabled = true;
    } else if (saveButton && document.querySelector(".content form[data-has-errors='true']")) {
      saveButton.disabled = false;
    }
    if (saveButton && isQueryMode) {
      saveButton.disabled = true;
    }
    if (newButton) {
      const inlineFormsetTable = getInlineFormsetTable();
      newButton.hidden = !(document.body.dataset.newUrl || tableForm || inlineFormsetTable);
      newButton.disabled = isQueryMode || !(document.body.dataset.newUrl || tableForm || inlineFormsetTable);
    }
    if (continueButton) {
      continueButton.hidden = !document.body.dataset.continueUrl;
      continueButton.disabled = isQueryMode || !document.body.dataset.continueUrl;
    }
    if (removeButton) removeButton.disabled = isQueryMode || (hasContextualRemoveTargets
      ? !contextualRemoveTarget
      : tableForm
        ? !hasSelectedPersistedRow(tableForm)
        : !(document.body.dataset.canRemove === "true" && hasLoadedRecord()));
    if (removeButton) removeButton.hidden = !(document.body.dataset.canRemove === "true" || tableForm || hasContextualRemoveTargets);
    const toggleActiveButton = document.querySelector('[data-action="toggle-active"]');
    if (toggleActiveButton) {
      const rowActiveField = getSelectedRowActiveField(tableForm);
      toggleActiveButton.hidden = !(rowActiveField || document.body.dataset.toggleActiveUrl);
      toggleActiveButton.disabled = !(rowActiveField || (document.body.dataset.toggleActiveUrl && hasLoadedRecord()));
      if (rowActiveField) {
        toggleActiveButton.title = rowActiveField.value === "true" ?"Desativar" : "Ativar";
      }
      toggleActiveButton.querySelector("[data-nav-icon]")?.setAttribute(
        "data-nav-icon",
        toggleActiveButton.title === "Ativar" ?"check" : "ban"
      );
    }
    const changePasswordButton = document.querySelector('[data-action="change-password"]');
    if (changePasswordButton) {
      changePasswordButton.hidden = !document.body.dataset.passwordUrl;
      changePasswordButton.disabled = !document.body.dataset.passwordUrl || !hasLoadedRecord();
    }
    if (reloadButton) {
      reloadButton.hidden = !document.body.dataset.reloadUrl;
      reloadButton.disabled = !document.body.dataset.reloadUrl;
    }
    if (printButton) {
      const hasSelectablePrintTarget = Boolean(document.querySelector("[data-toolbar-print-url]"));
      printButton.hidden = !(document.body.dataset.printUrl || hasSelectablePrintTarget);
      printButton.disabled = !document.body.dataset.printUrl;
    }
    if (previousButton) {
      previousButton.disabled = !document.body.dataset.previousUrl;
    }
    if (nextButton) {
      nextButton.disabled = !document.body.dataset.nextUrl;
    }
    if (firstButton) {
      firstButton.disabled = !document.body.dataset.firstUrl;
    }
    if (lastButton) {
      lastButton.disabled = !document.body.dataset.lastUrl;
    }
    if (closeButton && isHome) closeButton.disabled = true;
    if (cancelQueryIcon) cancelQueryIcon.setAttribute("data-nav-icon", "ban");
    const closeButtonIcon = document.querySelector('[data-action="close"] [data-nav-icon]');
    if (closeButtonIcon && document.body.dataset.closeMode === "back") {
      closeButtonIcon.setAttribute("data-nav-icon", "corner-up-left");
      document.querySelector('[data-action="close"]')?.setAttribute("title", "Voltar");
    }
  }

  function setupNotifications() {
    const now = new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
    document.querySelectorAll("[data-notification-time]").forEach((element) => {
      element.textContent = now;
    });
    const firstMessage = document.querySelector("[data-server-notification]");
    if (firstMessage) {
      const message = firstMessage.querySelector(".notification-text")?.textContent?.trim();
      const type = firstMessage.classList.contains("error")
        ?"error"
        : firstMessage.classList.contains("warning")
          ?"warning"
          : "info";
      if (message) {
        persistNotification(message, type);
        showBlockingNotification({
          title: type === "error" ?"Erro" : type === "warning" ?"Alerta" : "Informação",
          message,
          confirmText: "OK",
          type,
          focusTarget: type === "error" ?document.querySelector('[aria-invalid="true"]') : null,
        });
      }
    }
    renderPersistedNotifications();
  }

  function setupReadonlyLockedForms() {
    document.querySelectorAll("form[data-readonly-lock='true']").forEach((form) => {
      form.classList.add("form-readonly-lock");
      form.querySelectorAll("input, select, textarea, button").forEach((field) => {
        if (field.name === "csrfmiddlewaretoken" || field.type === "hidden") return;
        if (field.matches("button")) {
          field.disabled = true;
          return;
        }
        if (field.matches("select, input[type='checkbox'], input[type='radio']")) {
          field.disabled = true;
        } else {
          field.readOnly = true;
        }
      });
    });
  }

  function setupRecordLockRelease() {
    const form = document.querySelector("form[data-record-lock-release-url], form[data-table]");
    if (!form) return;
    form.dataset.lockReleaseReady = form.dataset.lockReleaseReady || "false";
  }

  function getRecordLockResource(form) {
    if (!form || !form.dataset.table || form.method?.toLowerCase() === "get") return null;
    const activeRow = form.matches("[data-editable-table]") ? getActiveEditableRow() : null;
    const primaryField = activeRow?.querySelector("[data-primary-key='true']")
      || form.querySelector("[data-primary-key='true'], .pk-label input");
    const resourceId = String(primaryField?.value || "").trim()
      || form.dataset.userId
      || form.dataset.providerId
      || `${window.location.pathname}${window.location.search}`;
    if (!resourceId) return null;
    return {
      tipo: form.dataset.table,
      resourceId,
      titulo: `${form.dataset.table} ${resourceId}`,
    };
  }

  function appendRecordLockPayload(payload, form) {
    const resource = getRecordLockResource(form);
    if (!resource) return false;
    payload.append("tipo", resource.tipo);
    payload.append("recurso_id", resource.resourceId);
    payload.append("titulo", resource.titulo);
    return true;
  }

  function lockFormForReadonly(form, message) {
    if (!form) return;
    form.dataset.readonlyLock = "true";
    form.dataset.lockMessage = message || form.dataset.lockMessage || "Este registro estÃ¡ bloqueado para ediÃ§Ã£o por outro usuÃ¡rio.";
    form.classList.add("form-readonly-lock");
    form.querySelectorAll("input, select, textarea, button").forEach((field) => {
      if (field.name === "csrfmiddlewaretoken" || field.type === "hidden") return;
      if (field.matches("button")) {
        field.disabled = true;
      } else if (field.matches("select, input[type='checkbox'], input[type='radio']")) {
        field.disabled = true;
      } else {
        field.readOnly = true;
      }
    });
    const saveButton = document.querySelector('[data-action="save"]');
    if (saveButton) saveButton.disabled = true;
  }

  async function ensureCurrentRecordLock(form) {
    if (!form || form.dataset.lockReleaseReady === "true") return true;
    const acquireUrl = form.dataset.recordLockAcquireUrl || (getRecordLockResource(form) ?"/travas/adquirir/" : "");
    if (!acquireUrl) return true;
    if (!formHasActualChanges(form)) return true;
    if (form.dataset.lockAcquirePending === "true") return false;
    const csrfToken = form.querySelector("[name='csrfmiddlewaretoken']")?.value || "";
    form.dataset.lockAcquirePending = "true";
    try {
      const lockPayload = new FormData(form);
      appendRecordLockPayload(lockPayload, form);
      const response = await fetch(acquireUrl, {
        method: "POST",
        credentials: "same-origin",
        body: lockPayload,
        headers: csrfToken ? { "X-CSRFToken": csrfToken, "Accept": "application/json" } : { "Accept": "application/json" },
      });
      let payload = {};
      try {
        payload = await response.json();
      } catch (error) {
        payload = {};
      }
      if (!response.ok || payload.ok === false) {
        const message = payload.error || "Este registro estÃ¡ bloqueado para ediÃ§Ã£o por outro usuÃ¡rio.";
        addNotificationToHistory(message, "warning", false);
        lockFormForReadonly(form, message);
        return false;
      }
      form.dataset.lockReleaseReady = "true";
      return true;
    } catch (error) {
      addNotificationToHistory("NÃ£o foi possÃ­vel validar a trava de ediÃ§Ã£o. Tente novamente.", "error", false);
      return false;
    } finally {
      delete form.dataset.lockAcquirePending;
    }
  }

  async function releaseCurrentRecordLock() {
    const form = document.querySelector("form[data-lock-release-ready='true']");
    if (!form) return;
    const releaseUrl = form.dataset.recordLockReleaseUrl || "/travas/liberar/";
    const csrfToken = form.querySelector("[name='csrfmiddlewaretoken']")?.value || "";
    if (!releaseUrl) return;
    form.removeAttribute("data-lock-release-ready");
    const payload = new FormData();
    payload.append("csrfmiddlewaretoken", csrfToken);
    appendRecordLockPayload(payload, form);
    try {
      await fetch(releaseUrl, {
        method: "POST",
        body: payload,
        credentials: "same-origin",
        headers: csrfToken ? { "X-CSRFToken": csrfToken } : {},
      });
    } catch (error) {
      form.dataset.lockReleaseReady = "true";
    }
  }

  function setupSessionMonitor() {
    if (!document.body.dataset.username) return;
    const documentEditor = document.querySelector("[data-document-editor-form]");
    const checkSession = async () => {
      try {
        const statusUrl = documentEditor
          ?"/accounts/sessao/status/?editando_documento=1"
          : "/accounts/sessao/status/";
        const response = await fetch(statusUrl, {
          headers: { "Accept": "application/json" },
          credentials: "same-origin",
        });
        if (response.status === 401) {
          let payload = {};
          try {
            payload = await response.json();
          } catch (error) {
            payload = {};
          }
          clearUserRuntimeState();
          const loginUrl = new URL(payload.login_url || "/accounts/login/", window.location.origin);
          loginUrl.searchParams.set("next", `${window.location.pathname}${window.location.search}${window.location.hash}`);
          window.location.replace(loginUrl.toString());
        }
      } catch (error) {
        // Falha transitória de rede não encerra a sessão local imediatamente.
      }
    };
    checkSession();
    window.setInterval(checkSession, documentEditor ?30000 : 60000);
    document.addEventListener("visibilitychange", () => {
      if (!document.hidden) checkSession();
    });
  }

  function disableBrowserAutocomplete() {
    document.querySelectorAll("form").forEach((form, formIndex) => {
      form.setAttribute("autocomplete", "off");
      form.setAttribute("data-form-type", "other");
      form.dataset.autocompleteSection = form.dataset.autocompleteSection || `celeris-${formIndex}-${Date.now()}`;
    });
    document.querySelectorAll("input, textarea, select").forEach((field, fieldIndex) => {
      const form = field.closest("form");
      const type = (field.getAttribute("type") || "").toLowerCase();
      const shouldPreserveNativeAutocomplete = Boolean(
        field.matches("[data-company-user]")
        || type === "password"
      );
      if (!shouldPreserveNativeAutocomplete) {
        const section = form?.dataset.autocompleteSection || "celeris";
        field.setAttribute("autocomplete", `section-${section}-${fieldIndex} new-password`);
      }
      field.setAttribute("autocapitalize", "off");
      field.setAttribute("spellcheck", "false");
      field.setAttribute("aria-autocomplete", "none");
      field.setAttribute("data-lpignore", "true");
      field.setAttribute("data-1p-ignore", "true");
    });
  }

  function setupUserLoginSuggestion() {
    const fullNameField = document.querySelector("[data-user-full-name]");
    const loginField = document.querySelector("[data-user-login]");
    const userForm = fullNameField?.closest(".user-form");
    if (!fullNameField || !loginField || !userForm || userForm.dataset.userId) return;
    let timer;
    let requestSequence = 0;
    loginField.value = "";
    window.setTimeout(() => {
      if (!fullNameField.value.trim()) loginField.value = "";
    }, 200);
    fullNameField.addEventListener("input", () => {
      if (document.body.classList.contains("screen-query-mode")) return;
      window.clearTimeout(timer);
      const sequence = ++requestSequence;
      timer = window.setTimeout(async () => {
        const params = new URLSearchParams({ nome: fullNameField.value });
        const response = await fetch(`/accounts/usuarios/login-sugerido/?${params.toString()}`);
        const payload = await response.json();
        if (sequence !== requestSequence) return;
        loginField.value = payload.login || "";
      }, 250);
    });
    userForm.addEventListener("celeris:reset-multiselects", () => {
      requestSequence += 1;
      window.clearTimeout(timer);
      loginField.value = "";
    });
  }

  function focusFirstEditableField() {
    if (shouldStartInQueryMode()) return;
    const field = document.querySelector('[name="nm_paciente"]:not([disabled]):not([readonly])')
      || document.querySelector(".content form input:not([type='hidden']):not([disabled]):not([readonly]), .content form select:not([disabled]), .content form textarea:not([disabled]):not([readonly])");
    if (!field) return;
    field.focus();
    field?.select?.();
  }

  function renderTabs() {
    const tabsBar = document.querySelector(".tabs-bar");
    const title = document.body.dataset.tabRootTitle || document.body.dataset.tabTitle || "Início";
    const url = `${window.location.pathname}${window.location.search}`;
    const key = document.body.dataset.tabKey || url;
    if (!tabsBar) return;

    const homeTab = { title: "Início", url: "/" };
    let savedTabs = [];
    try {
      savedTabs = JSON.parse(localStorage.getItem("celeris-tabs") || "[]");
    } catch (error) {
      savedTabs = [];
    }
    const tabs = [
      homeTab,
      ...savedTabs.filter((tab) => (
        tab.key !== homeTab.url
        && tab.url !== homeTab.url
        && (tab.key === key || tab.title !== title)
      )),
    ];
    const currentIndex = tabs.findIndex((tab) => (tab.key || tab.url) === key);

    if (currentIndex >= 0) {
      tabs[currentIndex] = { title, url, key };
    } else {
      if (tabs.length >= 10) {
        const fallbackTab = tabs[tabs.length - 1] || homeTab;
        showBlockingNotification({
          title: "Limite de guias abertas",
          message: "Você atingiu o limite de 10 guias abertas. Feche alguma guia para abrir novas telas.",
          confirmText: "OK",
          type: "info",
        }).then(() => {
          if (key !== (fallbackTab.key || fallbackTab.url)) window.location.href = fallbackTab.url;
        });
        return;
      }
      tabs.push({ title, url, key });
    }

    const limitedTabs = [homeTab, ...tabs.filter((tab) => (tab.key || tab.url) !== homeTab.url)].slice(0, 10);
    localStorage.setItem("celeris-tabs", JSON.stringify(limitedTabs.filter((tab) => (tab.key || tab.url) !== homeTab.url)));

    tabsBar.innerHTML = limitedTabs.map((tab) => {
      const tabKey = tab.key || tab.url;
      const active = tabKey === key || (tab.url === "/" && title === "Início");
      const closeButton = tab.url === homeTab.url ?"" : `<button class="tab-close" data-tab-close data-tab-url="${escapeHTML(tab.url)}" data-tab-key="${escapeHTML(tabKey)}" type="button" title="Fechar guia">&times;</button>`;
      return `<a class="tab${active ?" active" : ""}" href="${escapeHTML(tab.url)}"><span>${escapeHTML(tab.title)}</span>${closeButton}</a>`;
    }).join("");
  }

  function getStoredTabs() {
    try {
      return JSON.parse(localStorage.getItem("celeris-tabs") || "[]");
    } catch (error) {
      return [];
    }
  }

  function setStoredTabs(tabs) {
    localStorage.setItem("celeris-tabs", JSON.stringify(tabs.filter((tab) => (tab.key || tab.url) !== "/")));
  }

  function getCurrentFormStateKey(form = getPrimaryForm()) {
    if (!form || !form.matches(".content form") || form.hasAttribute("data-disable-state-persistence")) return "";
    const key = form.matches("[data-editable-table]")
      ?`${window.location.pathname}${window.location.search}`
      : document.body.dataset.tabKey || window.location.pathname;
    const userKey = document.body.dataset.username || "anon";
    const recordKey = form.dataset.providerId !== undefined
      ?`prestador:${form.dataset.providerId || "novo"}`
      : "";
    return `celeris-form-state:${userKey}:${key}${recordKey ? `:${recordKey}` : ""}`;
  }

  function getFormStateFields(form) {
    return Array.from(form.elements).filter((field) => (
      field.name
      && field.type !== "hidden"
      && field.name !== "csrfmiddlewaretoken"
      && field.type !== "password"
      && !field.disabled
    ));
  }

  function persistCurrentFormState(form = getPrimaryForm()) {
    const storageKey = getCurrentFormStateKey(form);
    if (!storageKey) return;
    const fields = getFormStateFields(form).map((field) => ({
      name: field.name,
      type: field.type || field.tagName.toLowerCase(),
      checked: Boolean(field.checked),
      value: field instanceof HTMLSelectElement && field.multiple
        ?Array.from(field.selectedOptions).map((option) => option.value)
        : field.value,
    }));
    localStorage.setItem(storageKey, JSON.stringify({ fields }));
  }

  function clearCurrentFormState(form = getPrimaryForm()) {
    const storageKey = getCurrentFormStateKey(form);
    if (storageKey) localStorage.removeItem(storageKey);
  }

  function restoreCurrentFormState(form = getPrimaryForm()) {
    const storageKey = getCurrentFormStateKey(form);
    if (!storageKey || document.body.dataset.formErrors !== "{}") return;
    let payload = null;
    try {
      payload = JSON.parse(localStorage.getItem(storageKey) || "null");
    } catch (error) {
      payload = null;
    }
    if (!payload?.fields?.length) return;
    if (form.matches("[data-editable-table]")) {
      const templateFieldNames = new Set(
        Array.from(form.querySelector("template[data-table-new-row]")?.content.querySelectorAll("[name]") || [])
          .map((field) => field.name)
          .filter(Boolean)
      );
      const requiredCounts = payload.fields.reduce((counts, field) => {
        if (!templateFieldNames.has(field.name)) return counts;
        counts[field.name] = Math.max(
          counts[field.name] || 0,
          payload.fields.filter((item) => item.name === field.name).length
        );
        return counts;
      }, {});
      let safety = 20;
      while (
        safety > 0
        && Object.entries(requiredCounts).some(([name, count]) => (
          form.querySelectorAll(`[name="${CSS.escape(name)}"]`).length < count
        ))
      ) {
        addEditableTableRow(form, false);
        safety -= 1;
      }
    }
    const fieldsByName = payload.fields.reduce((groups, field) => {
      groups[field.name] = groups[field.name] || [];
      groups[field.name].push(field);
      return groups;
    }, {});
    isRestoringFormState = true;
    try {
      Object.entries(fieldsByName).forEach(([name, savedFields]) => {
        const fields = Array.from(form.querySelectorAll(`[name="${CSS.escape(name)}"]`));
        fields.forEach((field, index) => {
          const saved = savedFields[index];
          if (!saved) return;
          if (field instanceof HTMLSelectElement && field.multiple && Array.isArray(saved.value)) {
            Array.from(field.options).forEach((option) => {
              option.selected = saved.value.includes(option.value);
            });
          } else if (field.matches('input[type="checkbox"], input[type="radio"]')) {
            field.checked = saved.checked;
          } else {
            field.value = saved.value ?? "";
          }
          field.dispatchEvent(new Event("change", { bubbles: true }));
        });
      });
    } finally {
      isRestoringFormState = false;
    }
    if (form.method?.toLowerCase() !== "get") {
      form.dataset.dirty = "true";
      const saveButton = document.querySelector('[data-action="save"]');
      if (saveButton) saveButton.disabled = false;
    }
  }

  function storeCurrentListPosition() {
    const storageKey = `celeris-list-scroll:${window.location.pathname}${window.location.search}`;
    const tableCard = document.querySelector("form.table-card[data-editable-table], .table-card");
    sessionStorage.setItem(storageKey, JSON.stringify({
      windowY: window.scrollY,
      tableTop: tableCard?.scrollTop || 0,
      tableLeft: tableCard?.scrollLeft || 0,
    }));
  }

  function setupListContextPreservation() {
    const storageKey = `celeris-list-scroll:${window.location.pathname}${window.location.search}`;
    document.querySelectorAll("[data-preserve-list-context]").forEach((link) => {
      link.addEventListener("click", storeCurrentListPosition);
    });
    document.querySelectorAll(".table-pager-link[href]").forEach((link) => {
      link.addEventListener("click", storeCurrentListPosition);
    });
    const storedPosition = sessionStorage.getItem(storageKey);
    if (storedPosition !== null) {
      window.requestAnimationFrame(() => {
        let payload = {};
        try {
          payload = JSON.parse(storedPosition);
        } catch (error) {
          payload = { windowY: Number(storedPosition) || 0 };
        }
        window.scrollTo(0, Number(payload.windowY) || 0);
        const tableCard = document.querySelector("form.table-card[data-editable-table], .table-card");
        if (tableCard) {
          tableCard.scrollTop = Number(payload.tableTop) || 0;
          tableCard.scrollLeft = Number(payload.tableLeft) || 0;
        }
      });
      sessionStorage.removeItem(storageKey);
    }
  }

  function closeTab(tabUrl, tabKey = tabUrl) {
    const currentKey = document.body.dataset.tabKey || document.body.dataset.tabUrl || "/";
    const userKey = document.body.dataset.username || "anon";
    const formStatePrefix = `celeris-form-state:${userKey}:${tabKey}`;
    Object.keys(localStorage)
      .filter((key) => key === formStatePrefix || key.startsWith(`${formStatePrefix}?`))
      .forEach((key) => localStorage.removeItem(key));
    const tabs = getStoredTabs().filter((tab) => (tab.key || tab.url) !== tabKey);
    setStoredTabs(tabs);
    if (tabKey === currentKey) {
      const nextTab = tabs[tabs.length - 1];
      window.location.href = nextTab?.url || "/";
    } else {
      renderTabs();
    }
  }

  function closeCurrentTab() {
    const currentUrl = document.body.dataset.tabUrl || "/";
    const currentKey = document.body.dataset.tabKey || currentUrl;
    if (currentUrl === "/") {
      window.location.href = "/";
      return;
    }
    closeTab(currentUrl, currentKey);
  }

  function shouldStartInQueryMode() {
    return (
      document.body.dataset.startQuery === "true"
      && !document.querySelector(".content form[data-editable-table]")
    );
  }

  renderTabs();
  setupListContextPreservation();
  setupSpecialtyManager();
  setupScaleProviderSpecialties();
  setupAssignmentManagers();
  setupRoleModuleVisibility();
  setupStandardCheckboxes();
  setupFormSectionAccordion();
  setupNavigationBuilder();
  setupCallIconTables();
  setupSystemIconPickers();
  setupSortableTables();
  setupResizableTables();
  setupCepCityDependencies();
  setupInitialEditableRows();
  updateTablePagerVisibility();
  if (document.body.dataset.formErrors === "{}") {
    document.querySelectorAll(".content form").forEach((form) => {
      initialFormSignatures.set(form, formValueSignature(form));
    });
  }
  if (!shouldStartInQueryMode() && !sessionStorage.getItem("celeris-open-query-after-save")) {
    restoreCurrentFormState();
  }
  const warNameField = document.querySelector("[data-war-name]");
  if (warNameField?.value.trim()) {
    warNameField.dataset.manuallyEdited = "true";
  }
  const sameAddressField = document.querySelector("[data-same-address]");
  if (sameAddressField) {
    copyResidentialAddressToCommercial(sameAddressField.checked);
    [
      "cd_cep",
      "sg_estado",
      "ds_cidade",
      "tp_logradouro",
      "ds_endereco",
      "nr_endereco",
      "ds_complemento",
      "ds_bairro",
    ].forEach((fieldName) => {
      const field = document.querySelector(`[name="${fieldName}"]`);
      field?.addEventListener("input", () => {
        if (sameAddressField.checked) copyResidentialAddressToCommercial(true);
      });
      field?.addEventListener("change", () => {
        if (sameAddressField.checked) copyResidentialAddressToCommercial(true);
      });
    });
  }
  const currentDateTime = document.querySelector("[data-current-datetime]");
  if (currentDateTime) {
    const renderDateTime = () => {
      currentDateTime.textContent = new Date().toLocaleString("pt-BR");
    };
    renderDateTime();
    window.setInterval(renderDateTime, 1000);
  }
  setupActionButtons();
  scheduleSidebarAutoCollapse();
  const continueAfterSave = sessionStorage.getItem("celeris-continue-after-save");
  if (continueAfterSave && document.body.dataset.formErrors === "{}") {
    sessionStorage.removeItem("celeris-continue-after-save");
    window.location.href = continueAfterSave;
    return;
  }

  function setupSidebarSearch() {
    const search = document.querySelector("[data-sidebar-search]");
    const sidebar = search?.closest(".sidebar");
    if (!search || !sidebar) return;
    const normalize = (value) => String(value || "")
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLocaleLowerCase("pt-BR");
    let searchActive = false;
    let openStateBeforeSearch = new Map();
    const applyFilter = () => {
      const term = normalize(search.value.trim());
      const groups = [...sidebar.querySelectorAll(".nav-group, .nav-subgroup")];
      if (term && !searchActive) {
        openStateBeforeSearch = new Map(groups.map((group) => [group, group.open]));
        searchActive = true;
      }
      sidebar.querySelectorAll("a").forEach((link) => {
        link.hidden = Boolean(term) && !normalize(link.textContent).includes(term);
      });
      [...sidebar.querySelectorAll(".nav-subgroup")].reverse().forEach((group) => {
        const ownMatch = normalize(group.querySelector(":scope > summary .nav-label")?.textContent).includes(term);
        const visibleChild = [...group.querySelectorAll(":scope > div > a, :scope > div > details")]
          .some((item) => !item.hidden);
        group.hidden = Boolean(term) && !ownMatch && !visibleChild;
        if (term && !group.hidden) group.open = true;
      });
      sidebar.querySelectorAll(".nav-group").forEach((group) => {
        const ownMatch = normalize(group.querySelector(":scope > summary .nav-label")?.textContent).includes(term);
        const visibleChild = [...group.querySelectorAll(":scope > div > a, :scope > div > details")]
          .some((item) => !item.hidden);
        group.hidden = Boolean(term) && !ownMatch && !visibleChild;
        if (term && !group.hidden) group.open = true;
      });
      if (!term && searchActive) {
        groups.forEach((group) => {
          group.hidden = false;
          group.open = openStateBeforeSearch.get(group) || false;
        });
        sidebar.querySelectorAll("a").forEach((link) => { link.hidden = false; });
        searchActive = false;
        openStateBeforeSearch.clear();
      }
    };
    search.addEventListener("input", applyFilter);
    search.closest(".sidebar-search")?.addEventListener("click", () => {
      if (!root.classList.contains("sidebar-state-collapsed") && !shell?.classList.contains("sidebar-collapsed")) return;
      localStorage.setItem("celeris-sidebar", "expanded");
      root.classList.remove("sidebar-state-collapsed");
      shell?.classList.remove("sidebar-collapsed");
      requestAnimationFrame(() => search.focus());
    });
  }
  if (shouldStartInQueryMode() || sessionStorage.getItem("celeris-open-query-after-save") === "true") {
    sessionStorage.removeItem("celeris-open-query-after-save");
    clearFormFields(getPrimaryForm());
    setQueryMode(true);
    const firstField = document.querySelector(".content input:not([type='hidden']), .content select, .content textarea");
    firstField?.focus();
  } else {
    setQueryMode(false);
  }
  updateThemeToggleIcon();
  renderIcons();
  disableBrowserAutocomplete();
  setupUserLoginSuggestion();
  setupServerValidationErrors();
  setupNotifications();
  setupFormConfirmations();
  setupReadonlyLockedForms();
  setupRecordLockRelease();
  setupSessionMonitor();
  setupSidebarSearch();
  document.addEventListener("keydown", (event) => {
    if (event.defaultPrevented || event.altKey || event.ctrlKey || event.metaKey) return;
    const queryButton = document.querySelector("[data-query-toggle]");
    const cancelButton = document.querySelector("[data-query-cancel]");
    if (event.key === "F7" && queryButton?.dataset.queryMode !== "execute") {
      event.preventDefault();
      queryButton?.click();
    } else if (event.key === "F8" && queryButton?.dataset.queryMode === "execute") {
      event.preventDefault();
      queryButton.click();
    } else if (event.key === "Escape" && document.body.classList.contains("screen-query-mode")) {
      event.preventDefault();
      cancelButton?.click();
    }
  });
  const printPrompt = document.querySelector("[data-print-after-save]");
  if (printPrompt) {
    showBlockingNotification({
      title: "Atendimento gerado",
      message: "Deseja imprimir a ficha de atendimento agora?",
      confirmText: "Imprimir",
      cancelText: "Agora não",
      initialFocus: "cancel",
    }).then((confirmed) => {
      if (confirmed) window.open(printPrompt.dataset.printUrl, "_blank", "noopener");
    });
  }
  updateFieldStatus(null);
  focusFirstEditableField();
})();
