
var last_container = null
var to_search = ''
var search_bar = document.getElementById('search-bar')
var key_map = {}

function logKey(e) {

    key = e.key
    key_map[key] = true

    let grades_container = document.getElementById('grades-container')
    if (grades_container != null) {

        if (last_container == null || last_container != 'grades-container') {
            to_search = '' 
            last_container = 'grades-container'
        }

        // every lesson container except first (header)
        let lessons = [...document.getElementsByClassName('lesson-container')].slice(1)
        
        update_to_search(key)

        for (let i=0; i<lessons.length; i++) {
            if (lessons[i].children[2].innerHTML.startsWith(to_search)) {
                lessons[i].style.display = 'flex'
            }
            else {
                lessons[i].style.display = 'none'
            }
        }

    }

    else {
        let addendance_container = document.getElementById('addendance-stats-container')
        if (addendance_container != null) {

            if (last_container == null || last_container != 'addendance-stats-container') {
                to_search = ''
                last_container = 'addendance-stats-container'
            }

            // every lesson container except first (header)
            let lessons = [...document.getElementsByClassName('lesson-container')].slice(1)

            update_to_search(key)

            for (let i=0; i<lessons.length; i++) {
                if (lessons[i].children[0].innerHTML.startsWith(to_search)) {
                    lessons[i].style.display = 'flex'
                }
                else {
                    lessons[i].style.display = 'none'
                }
            }
            
        }
    }
}

function update_to_search(key) {
    if (key.length == 1) {
        to_search += key
    }
    else if (key_map['Control'] && key_map['Backspace']) {
        to_search = ''
    }
    else {
        to_search = to_search.slice(0, -1)
    }

    if (to_search == '') {
        search_bar.style.display = 'none'
    }
    else {
        search_bar.style.display = 'block'
        search_bar.innerHTML = to_search
    }
}
document.body.addEventListener('keydown', logKey)
document.body.addEventListener('keyup', e => key_map[e.key] = false)
