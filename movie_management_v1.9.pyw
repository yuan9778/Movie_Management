#! python3


from tkinter import *
from tkinter import ttk
from tkinter import filedialog, messagebox
from operator import itemgetter
import os, json, subprocess, shutil, requests, bs4, re, webbrowser, sys



def duration(filename):
    pipe = subprocess.Popen(["ffprobe", filename], stdout = subprocess.PIPE, stderr = subprocess.STDOUT)
    length = ''    

    for x in pipe.stdout.readlines():
        try:
            decoded = str(x)
            if "Duration" in decoded:
                length = decoded
                break
        except:
            return 0
    if length =='':
        return 0

    regex = re.compile(r'Duration: (\d\d):(\d\d):(\d\d).\d\d')
    mo = regex.search(length)
    if mo != None:
        hours = int(mo.group(1))
        mins = int(mo.group(2))
        second = int(mo.group(3))
        if second >= 30:
            second = 1
        else:
            second = 0
        return hours*60 + mins + second
    else:
        return 0


def sizeConverter(byte_size):
	if byte_size < 1024:
		return str(byte_size) + "byte"
	elif byte_size < 1048576:
		return str(int(byte_size/1024)) + "Kb"
	elif byte_size < 1073741824:
		return str(int(byte_size/1048576)) + "Mb"
	else:
		return str(byte_size/1073741824)[:4] + "Gb"

def scan_directory():
    # make sure switch to whole database mode
    global whole_db    
    whole_db = True
    
    # select a directory from local storage
    dirname = filedialog.askdirectory()

    root.geometry('500x300')
    # a valid directory is selected
    # if no directory selected, do nothing
    if dirname !='':
	# a temparary dictionary to store movie info from this directory
        movie_db = {}
        size_db = 0

        # this is for scan directory menu
        # it can add more movie record to current json file
        # load current movie database from local json file
        if os.path.exists('movies_db.json'):
            movieFile = open('movies_db.json', 'r')
            movieString = movieFile.read()
            movie_db = json.loads(movieString)
            movieFile.close()
            size_db = len(movie_db)
        
        # walk through the selected directory finding video files
        for folderName, subfolders, filenames in os.walk(dirname):  
            for filename in filenames:
 		# parse filename into file name and extension
                vnRegex = re.compile(r'^(.+)\.(\w{2,10})$')
                mo = vnRegex.search(filename)
                if mo!=None:
                    file_title = mo.group(1)
                    extention = mo.group(2)
                    extention = extention.lower()
                    # only find video files that not already in database
                    if (file_title not in movie_db.keys()) and (extention in video_format):
                        file_path = os.path.join(folderName, filename)    
                        file_size = os.path.getsize(file_path)
                        length = duration(file_path)
                        record = {'genres': '', 'director':'', 'star':'', 'runtime':length, \
                                  'path':folderName, 'poster':'NA', 'trailer':'NA', 'restriction':'',
                                  'year':'NA', 'writers':'', 'storyline':'','verified':'x', \
                                  'extention':extention, 'size':file_size, 'link':'', 'rating':'NA'}
                        movie_db[file_title] = record
             
        # database not empty
        if len(movie_db) > 0:
            # found new video files
            if len(movie_db) > size_db:
                # update movie records in json file, don't need to delete current json file
                # if 'w' mode is used, it will replaced curent content.
                # If no such json file, it will create one.
                moviesdbFile = open('movies_db.json', 'w')
                moviesdbFile.write(json.dumps(movie_db))
                moviesdbFile.close()
            # display all movie record in treeview
            create_treelistview()
        # didn't find any video files,just go back to scan window
        else: 
            label_content.set("No video file found in this directory. Please scan other directory")

def add_movie():
    # make sure switch to whole database mode
    global whole_db    
    whole_db = True
    
    filename = filedialog.askopenfilename()
    if filename != '':
        movie_db = {}
        size_db = 0
        if os.path.exists('movies_db.json'):
            movieFile = open('movies_db.json')
            movieString = movieFile.read()
            movie_db = json.loads(movieString)
            movieFile.close()
            size_db = len(movie_db)
        base_name = os.path.basename(filename)
        path = os.path.dirname(filename)
        vnRegex = re.compile(r'^(.+)\.(\w{2,10})$')
        mo = vnRegex.search(base_name)
        file_title = mo.group(1)
        extention = mo.group(2)
        if (base_name not in movie_db.keys()) and (extention in video_format):
            file_size = os.path.getsize(filename)
            length = duration(filename)
            record = {'genres': '', 'director':'', 'star':'', 'runtime':length, 'path':path, 'poster':'NA', \
                      'trailer':'NA', 'restriction':'', 'year':'NA', 'writers':'', 'storyline':'NA','verified':'x',\
                      'extention':extention, 'size':file_size, 'link':'', 'rating':'NA'}
            movie_db[file_title] = record 
        if len(movie_db) > 0:
            if len(movie_db) > size_db:
                moviesdbFile = open('movies_db.json', 'w')
                moviesdbFile.write(json.dumps(movie_db))
                moviesdbFile.close()
            create_treelistview()
        

def play(event):
    global tree
    if os.path.exists('movies_db.json')==False:
        messagebox.showwarning(title="Warning", message="no database found!", icon="warning")
    global movieDict
    if tree.focus() != '':
        filepath = os.path.join(movieDict[tree.focus()]['path'], tree.focus()) + "." + movieDict[tree.focus()]['extention']
        if sys.platform.startswith('darwin'):
            subprocess.call(('open', filepath))
        elif os.name == 'nt':
            os.startfile(filepath)
        elif os.name == 'posix':
            subprocess.call(('xdg-open', filepath))
        
def display_order(head):
    global sorted_by, is_reverse
    sorted_by = head
    if is_reverse:
        is_reverse = False
    else:
        is_reverse = True
    create_treelistview()

def create_treelistview():
       
    # hide scan frame    
    start_frame.grid_remove()

    # remove previous treelistview
    global tree, frame,scrollbar
    global movieDict, newlist, heading_display, is_reverse, whole_db, list_ret, keywords
    if tree!=None:
        tree.grid_remove()
        frame.grid_remove()

    # load most recent data from json file
    movieFile = open('movies_db.json', 'r')
    movieString = movieFile.read()
    movieFile.close()    
    movieDict = json.loads(movieString)

    # generate list of dict for sorting purpose
    newlist = []  # need to clear newlist
    for key in movieDict.keys():
        dict_temp = movieDict[key]
        dict_temp['title'] = key
        newlist.append(dict_temp)

    # for search result, assign newlist with list_ret
    if whole_db==False:
        newlist=list_ret
        root.title("Search results for: " + '/'.join(keywords))

    # sort list of dict by a specific key
    newlist = sorted(newlist, key=itemgetter(sorted_by), reverse=is_reverse)
        
    # create current treelistview
    c_d = tuple(heading_display)
    tree = ttk.Treeview(root, columns = c_d, height = 30)
    
    
    tree.column('#0', width = 10, stretch=False)
    # set up selected columns
    if 'title' in heading_display:
        tree.column('title', width = 400)
        tree.heading('title', text='Title', anchor = W, command=lambda:display_order('title'))

    if 'extention' in heading_display:    
        tree.column('extention', width = 20)
        tree.heading('extention', text='Extention', anchor = W, command=lambda:display_order('extention'))

    if 'director' in heading_display:
        tree.column('director', width = 50)
        tree.heading('director', text='Director', anchor = W, command=lambda:display_order('director'))

    if 'star' in heading_display:
        tree.column('star', width = 50)
        tree.heading('star', text='Star', anchor = W, command=lambda:display_order('star'))

    if 'size' in heading_display:
        tree.column('size', width = 30)
        tree.heading('size', text='Size', anchor = W, command=lambda:display_order('size'))

    if 'path' in heading_display:
        tree.column('path', width = 250)
        tree.heading('path', text='Path', anchor = W, command=lambda:display_order('path'))

    if 'verified' in heading_display:
        tree.column('verified', width = 30)
        tree.heading('verified', text='Verified', anchor = W, command=lambda:display_order('verified'))

    if 'year' in heading_display:
        tree.column('year', width = 30)
        tree.heading('year', text='Year', anchor = W, command=lambda:display_order('year'))

    if 'runtime' in heading_display:
        tree.column('runtime', width = 50)
        tree.heading('runtime', text='Duration (mins)', anchor = W, command=lambda:display_order('runtime'))

    if 'writers' in heading_display:
        tree.column('writers', width = 100)
        tree.heading('writers', text='Writers', anchor = W, command=lambda:display_order('writers'))

    if 'rating' in heading_display:
        tree.column('rating', width = 30)
        tree.heading('rating', text='Rating', anchor = W, command=lambda:display_order('rating'))

    if 'genres' in heading_display:
        tree.column('genres', width = 60)
        tree.heading('genres', text='Genre', anchor = W, command=lambda:display_order('genres'))

    # insert tree items into treeview
    for i in range(len(newlist)):
        value_displayed = []
        for val in heading_display:
            if val=='size':
                value_displayed.append(sizeConverter(newlist[i][val]))    
            else:
                value_displayed.append(newlist[i][val])    
        tree.insert('', 'end', newlist[i]['title'], value=tuple(value_displayed), tags=str(int(i%2)))

    # set up bg color for odd and even rows
    global width, height
    if root.winfo_width()>10:
        width = root.winfo_width()
        height = root.winfo_height()
    root.geometry(str(width)+'x'+str(height))
    tree.tag_configure('0', background='#ffffe6')
    tree.tag_configure('1', background='#e0ebeb')
    
    tree.grid(column = 0, row = 0, columnspan=2, sticky=(N, W, E, S))

    # set up scrollbar for tree view
    scrollbar = ttk.Scrollbar(root, orient=VERTICAL, command=tree.yview)
    scrollbar.grid(column=2, row=0, sticky=(N, S))
    tree['yscrollcommand'] = scrollbar.set

    # resize settings
    tree.columnconfigure(0, weight=1)
    tree.rowconfigure(0, weight=1)

    # set up buttons below treeview
    frame = ttk.Frame(root)
    frame.grid(column=0, row=1, columnspan=2)
    play_button = ttk.Button(frame, text = "Play", command=lambda:play('')) 
    details_button = ttk.Button(frame, text = "Details", command=lambda:detail(tree))
    if whole_db==True:
        search_button = ttk.Button(frame, text="Search", command=search)
        search_button.grid(column = 2, row = 0, padx=5)
    else:
        back_button = ttk.Button(frame, text="Back", command=go_back)
        back_button.grid(column = 2, row = 0, padx=5)    
       
    play_button.grid(column = 0, row = 0, padx=5)
    details_button.grid(column = 1, row = 0, padx=5)

    global rightclick
    rightclick = Menu(tree, font='Cambria 14 bold', bg='#99ccff', fg='#333399')

    # right click contexual menu
    rightclick.add_command(label="Play", command=lambda:play(''))
    rightclick.add_command(label="Modify", command=modify_movie)
    rightclick.add_command(label="Delete", command=delete_movie)
    rightclick.add_command(label="Verify", command=lambda:match_one_movie(''))
    rightclick.add_command(label="Details", command=lambda:detail(tree))
    tree.bind('<3>', popup)
    tree.bind('<Double-Button-1>', play)


def popup(event):
    global tree, rightclick
    iid = tree.identify_row(event.y)
    if iid:
        items = []
        items.append(iid)
        tree.selection_set(items)
        tree.focus(iid)
        rightclick.post(event.x_root, event.y_root)
    else:
        pass

def go_back():
    global whole_db
    root.title('Lobal Movie Management')
    whole_db = True
    create_treelistview()
    

def delete_db():
    if os.path.exists('movies_db.json')==False:
        messagebox.showwarning(title="Warning", message="no database found!", icon="warning")
    else:
        result = messagebox.askyesno(message="Are you sure you want to delete current database?", title="Reset", icon="question")
        if result:
            # delete json file in hard drive    
            os.unlink('movies_db.json')

            # delete current treeview window
            global tree, scrollbar, frame
            tree.grid_remove()
            frame.grid_remove()
            scrollbar.grid_remove()

            # enable scan directory window
            root.geometry('500x300')
            start_frame.grid()
            label.grid()
            scan_button.grid()


def get_stat():
    if os.path.exists('movies_db.json'):
        num_movie = len(movieDict)
        num_verified = 0
        for movieNam in movieDict.keys():
            if movieDict[movieNam]['verified'] == '√':
                num_verified += 1
        stat_ret = "The total number of movies: " + str(num_movie) + "\nVerified: " + str(num_verified)
        messagebox.showinfo(title="Stat", message=stat_ret)
    else:
        messagebox.showinfo(title="Stat", message="No database found!")

def exit_program():
    root.destroy()

def readme():
    guide_window = Toplevel()
    guide_window.title("ReadMe")
    guide_window.geometry('750x300+400+300')
    guide_window.resizable(width=False, height=False)
    
    content = Text(guide_window, width=100, padx=15, pady=15, wrap="word", spacing1=2)
    content.insert('1.0',
                   'Introduction\n'\
                   'This program can organize all your movies in your local storage. '\
                   'Scan the directories where you store your movies and fetch '\
                   'the details including cast, genre, director and et al from IMDB/douban '\
                   'automatically. More importantly, you can search movies of your '\
                   'interest by keywords like genres, title, year or actors. With the '\
                   'cross-searching system, you can find the movie you want to watch '\
                   'instantly. Then with a mouse click you can start enjoying your '\
                   'movie. You can also add more movies into your database or just '\
                   'detele your current database and build a new one.\n\n'\
                   'Functions\n'\
                   'Scan a directory: it will scan the directory of your choice and '\
                   'add all movies into your database. The valid file should be a video '\
                   'file and at least 10Mb. If you already have that movie in your database, '\
                   'the new scanned one will be ignored.\n'\
                   'Add a movie: same as scan a directory. It just add one movie.\n'\
                   'Reset: it will delete your current database.\n'\
                   'Stat: it lists the number of movies in your database and number of '\
                   'movies that were verified.\n'\
                   'Exit: quit the program.\n')
    content.grid(column=1, row=0, sticky=(N,W,E,S))
    content.tag_configure('highlightline', background='yellow', font='helvetica 12 bold', relief='raised')
    content.tag_configure('underline', underline=1, relief='raised')
    content.tag_add('highlightline', '1.0', '1.12')
    content.tag_add('highlightline', '4.0', '4.10')
    content.tag_add('underline', '5.0', '5.16')
    content.tag_add('underline', '6.0', '6.11')
    content.tag_add('underline', '7.0', '7.5')
    content.tag_add('underline', '8.0', '8.4')
    content.tag_add('underline', '9.0', '9.4')
    content.config(state=DISABLED)


def about():
    about_window = Toplevel()
    about_window.title("About")
    about_window.geometry('300x150+400+300')
    about_window.resizable(width=False, height=False)
    about_info = 'Local Movie Management\n\nSanqing Yuan\n\nemail: sanqing.yuan@gmail.com'\
                 '\n\nversion: v1.1'
    content = Label(about_window, text=about_info, padx=20, pady=10, justify="left")
    content.grid()

def goto_(link_):
    if link_=='NA':
        messagebox.showwarning(title="Warning", message="Sorry, trailer not available for this movie!", icon="warning")
    else:
        webbrowser.open(link_)    


def detail(tree):
    if os.path.exists('movies_db.json')==False:
        messagebox.showwarning(title="Warning", message="no database found!", icon="warning")
    elif tree.focus()!='':
        details_root = Toplevel()
        details_root.title("Details")
        movie_title = tree.focus()

        # title
        title_txt = Text(details_root, wrap='word', spacing1=2, font=('Cambria', '20', 'bold'), \
                         foreground='#6699ff', width=55, height=1, bg='#f2f2f2', relief='flat')
        title_txt.insert('1.0', movie_title)

        # attribute
        attribute = str(movieDict[movie_title]['runtime']) + 'mins' + ' | ' + movieDict[movie_title]['genres'] + \
                    ' | ' + movieDict[movie_title]['year'] + ' | ' + movieDict[movie_title]['rating']
        attribute_label = ttk.Label(details_root, text=attribute)

        # poster and trailer
        # poster_label = ttk.Label(details_root, padding=(15,5,5,5))
        # trailer, douban and watch buttons
        button_frame = ttk.Button(details_root)
        trailer_button = ttk.Button(button_frame, text="Watch Trailer", width=15, padding=(15,5,5,5),\
                                    command=lambda:goto_(movieDict[tree.focus()]['trailer']))
        imdb_button = ttk.Button(button_frame, text="Douban page", width=15, padding=(15,5,5,5), \
                                 command=lambda:goto_(movieDict[tree.focus()]['link']))
        watch_button = ttk.Button(button_frame, text="Watch Now", width=15, padding=(15,5,5,5), command=lambda:play(''))

        # director, writer, cast and storyline
        director_txt = Text(details_root, wrap='word', spacing1=2, font=('Cambria', '16', 'bold'), \
                            width=90, height=1, bg='#f2f2f2', relief='flat')
        director_txt.insert('1.0', 'Director: ' + movieDict[movie_title]['director'])
        
        writer_txt = Text(details_root, wrap='word', spacing1=2, font=('Cambria', '16', 'bold'), \
                          width=90, height=1, bg='#f2f2f2', relief='flat')
        writer_txt.insert('1.0', 'Writers: ' + movieDict[movie_title]['writers'])
        cast_txt = Text(details_root, wrap='word', spacing1=2, font=('Cambria', '14'), width=90, \
                        height=3, bg='#f2f2f2', relief='flat')
        cast_txt.insert('1.0', "Cast: "+ movieDict[movie_title]['star'])
        
        storyline_txt = Text(details_root, wrap='word', spacing1=2, font=('Cambria', '14'), \
                             width=90, height=8, bg='#f2f2f2', relief='flat')
        storyline_txt.insert('1.0', "Storyline: "+ movieDict[movie_title]['storyline'])
        
        # path, format, size and verified
        path_txt = Text(details_root, wrap='word', spacing1=2, font=('Cambria', '16', 'bold'), \
                        width=90, height=1, bg='#f2f2f2', relief='flat')
        format_txt = Text(details_root, wrap='word', spacing1=2, font=('Cambria', '16', 'bold'), \
                          width=90, height=1, bg='#f2f2f2', relief='flat')
        size_txt = Text(details_root, wrap='word', spacing1=2, font=('Cambria', '16', 'bold'), \
                        width=90, height=1, bg='#f2f2f2', relief='flat')
        verified_txt = Text(details_root, wrap='word', spacing1=2, font=('Cambria', '16', 'bold'), \
                            width=90, height=1, bg='#f2f2f2', relief='flat')
        path_txt.insert('1.0', "Local location: "+movieDict[movie_title]['path'])
        format_txt.insert('1.0', "Video format: "+movieDict[movie_title]['extention'])
        size_txt.insert('1.0', "File size: "+sizeConverter(movieDict[movie_title]['size']))
        verified_txt.insert('1.0', "Verified: "+movieDict[movie_title]['verified'])

        
        details_root.columnconfigure(0, weight=1)
        details_root.rowconfigure(0, weight=1)
        
        title_txt.grid(column=0, row=0, padx=5, pady=5)        
        attribute_label.grid(column=0, row=1)        
        # poster_label.grid(column=0, row=2)

        button_frame.grid(column=0, row=3, pady=10)
        trailer_button.grid(column=0, row=0)
        imdb_button.grid(column=1, row=0)
        watch_button.grid(column=2, row=0)
        
        director_txt.grid(column=0, row=4, sticky=W, padx=40, pady=5)
        writer_txt.grid(column=0, row=5, sticky=W, padx=40, pady=5)
        cast_txt.grid(column=0, row=6, sticky=W, padx=40, pady=5)
        storyline_txt.grid(column=0, row=7, sticky=W, padx=40, pady=5)
        
        path_txt.grid(column=0, row=8, sticky=W, padx=40, pady=5)
        format_txt.grid(column=0, row=9, sticky=W, padx=40, pady=5)
        size_txt.grid(column=0, row=10, sticky=W, padx=40, pady=5)
        verified_txt.grid(column=0, row=11, sticky=W, padx=40, pady=5)
        

        # change appearance of different text widgets
        title_txt.tag_configure('center', justify='center')
        director_txt.tag_configure('keyword', foreground='#ff3300')
        writer_txt.tag_configure('keyword', foreground='#ff9900')
        cast_txt.tag_configure('keyword', foreground='#e6e600', font=('Cambria', '16', 'bold'))
        storyline_txt.tag_configure('keyword', foreground='#33cc33', font=('Cambria', '16', 'bold'))
        path_txt.tag_configure('keyword', foreground='#6699ff')
        format_txt.tag_configure('keyword', foreground='#000099')
        size_txt.tag_configure('keyword', foreground='#6600cc')
        title_txt.tag_add('center', '1.0', END)
        director_txt.tag_add('keyword', '1.0', '1.9')
        writer_txt.tag_add('keyword', '1.0', '1.8')
        cast_txt.tag_add('keyword', '1.0', '1.6')
        storyline_txt.tag_add('keyword', '1.0', '1.10')
        path_txt.tag_add('keyword', '1.0', '1.15')
        format_txt.tag_add('keyword', '1.0', '1.12')
        size_txt.tag_add('keyword', '1.0', '1.10')

        title_txt.config(state=DISABLED)
        director_txt.config(state=DISABLED)
        writer_txt.config(state=DISABLED)
        cast_txt.config(state=DISABLED)
        storyline_txt.config(state=DISABLED)
        path_txt.config(state=DISABLED)
        format_txt.config(state=DISABLED)
        size_txt.config(state=DISABLED)
        verified_txt.config(state=DISABLED)

        # scrollbar for storyline
        s = ttk.Scrollbar(details_root, orient=VERTICAL, command=storyline_txt.yview)
        s.grid(column=1, row=7, sticky=(N,S))
        storyline_txt['yscrollcommand'] = s.set


def combineEle(list_, ret):
    for i in range(len(ret)):
        list_.append(ret[i].getText())

def confirm_info(window, old_title, selection):
    if window!=None:
        window.destroy()

    html_content = requests.get(selection.get())
    soup = bs4.BeautifulSoup(html_content.text, "html.parser")
    ret = soup.select('h1 span')
    title = ret[0].getText()
    special_char = ['/', ':', '*', '?', '"', '<', '>', '|']
    list_str = list(title)
    
    # replace invalid chars in file name
    for i in range(len(list_str)):
        if list_str[i] in special_char:
            list_str[i] = '-'
    title = "".join(list_str)
    if title != old_title and title in movieDict.keys():
        messagebox.showwarning(title="Warning", message="title already in database!", icon="warning")
    else:
            # year
            year = ret[1].getText()
            yearRegex = re.compile(r'^\((\d{4})\)$')
            mo = yearRegex.search(year)
            if mo==None:
                year='NA'
            else:
                year = mo.group(1)

            # path, extention, size
            path = movieDict[old_title]['path']
            ext = movieDict[old_title]['extention']
            size = movieDict[old_title]['size']
            runtime = movieDict[old_title]['runtime']

            # genres
            ret = soup.select('#info span[property="v:genre"]')
            genres = []
            if ret!=[]:
                combineEle(genres, ret)

            # directors    
            ret = soup.select('#info a[rel="v:directedBy"]')
            directors = []
            combineEle(directors, ret)
            size_director = len(directors)

            # cast
            ret = soup.select('#info a[rel="v:starring"]')
            cast = []
            combineEle(cast, ret)
            size_cast = len(cast)

            # writers
            ret = soup.select('#info span span a')
            writers = []
            for i in range(size_director, len(ret)-size_cast):
                writers.append(ret[i].getText())    
            '''
            # runtime
            runtime = 0
            ret = soup.select('#info span[property="v:runtime"]')
            if ret!=[]:
                regex = re.compile(r'^(\d+)')
                mo = regex.search(ret[0].getText())
                if mo!=None:
                    runtime = int(mo.group(1))
            '''

            # poster
            ret = str(soup.select('.nbgnbg'))
            posterRegex = re.compile(r'^.+src="(.+?)".+$', re.S)
            mo = posterRegex.search(ret)
            poster = 'NA'
            if mo!=None:
                poster = mo.group(1)

            # trailer
            trailer = 'NA'
            ret = soup.select('.related-pic-video')
            if ret != []:
                ret = str(ret)    
                trailerRegex = re.compile(r'^.+href="(.+?)".+$', re.S)
                mo = trailerRegex.search(ret)
                trailer = mo.group(1)

            # storyline
            ret = soup.select('span[property="v:summary"]')
            storyline = 'NA'
            if ret != []:
                storyline = ret[0].getText()

            # rating            
            ret = soup.select('strong[property="v:average"]')
            rating = 'NA'
            if ret !=[]:
                rating = ret[0].getText() + '/10'
            
            del movieDict[old_title]
            record = {'genres': '/'.join(genres), 'director': '/'.join(directors), 'star': '/'.join(cast),\
                      'runtime': runtime, 'path':path, 'poster': poster, 'trailer': trailer, 'restriction':'',\
                      'year': year, 'writers': '/'.join(writers), 'storyline': storyline,'verified':'√',\
                      'extention':ext, 'size':size, 'link':selection.get(), 'rating':rating}
            movieDict[title] = record
            moviesdbFile = open('movies_db.json', 'w')
            moviesdbFile.write(json.dumps(movieDict))
            moviesdbFile.close()

            global map_q, list_ret
            if old_title in map_q.keys():
                record['title'] = title
                list_ret[map_q[old_title]] = record
                if title != old_title:
                    map_q[title] = map_q[old_title]                
                    del map_q[old_title]

            # rename the movie file in hard drive
            if title != old_title:
                shutil.move(os.path.join(path, old_title) + '.' + ext, os.path.join(path, title) + '.' + ext)

            # refresh display
            create_treelistview()

    

def cancel_confirm(window):
    window.destroy()


    
def query_submit(match_window, original_title, title_variable, query_db):
    match_window.destroy()
    # grab keywords
    title = title_variable.get()
    # grab database to be queried
    db = query_db.get()

    # insufficient info
    if title == '' or db == '':
        messagebox.showwarning(title="Warning", message="title and/or database missing!", icon="warning")
    elif db == 'Douban' or db=='IMDB':
        # metadata used in callback function
        metadata = []
        # for douban query
        if db == 'Douban':
            res = requests.get('https://movie.douban.com/subject_search?search_text=' + title)
            doubanSoup = bs4.BeautifulSoup(res.text, "html.parser")
            search_ret = doubanSoup.select('.nbg')
                    
            for tagob in search_ret:
                tagRegex = re.compile(r'.+href=["|\'](.+?)["|\'].+title=["|\'](.+?)["|\'].+src="(.+?)".+', re.S)
                mo = tagRegex.search(str(tagob))                
                dict_temp = {'link':mo.group(1), 'title':mo.group(2), 'pic':mo.group(3)}
                metadata.append(dict_temp)
        # for IMDB query
        else:
            res = requests.get('http://www.imdb.com/find?q=' + title)
            imdbSoup = bs4.BeautifulSoup(res.text, "html.parser")
            search_ret_photo = imdbSoup.select('.primary_photo')
            search_ret_title = imdbSoup.select('.result_text')
            
        if len(metadata)==0:
            messagebox.showwarning(title="Warning", message="No record found!", icon="warning")
        else:
            search_ret = Toplevel()
            search_ret.title('Search result')
            intro = 'Search for ' + '"' + title + '"\n'+ 'Below is the search result from ' \
                    + db + '.com.\n' + 'Please select the correct one.'

            intro_label = ttk.Label(search_ret, text = intro, padding=(30, 25, 10, 10))
            intro_label.grid(column=0, row=0, columnspan=3)

            selection = StringVar()
            i = 0
            for i in range(len(metadata)):
                rb = ttk.Radiobutton(search_ret, text=metadata[i]['title'], variable=selection, \
                                     value=metadata[i]['link'],padding=(20, 5, 0, 5))
                link_button = ttk.Button(search_ret, text="link", command=lambda: callback(search_ret, metadata, 173, 29, 1))
                rb.grid(column=0, row=i+1, sticky=W)
                link_button.grid(column=1, row=i+1, sticky=W)
                    
            confirm_button = ttk.Button(search_ret, text="Confirm", command=lambda:confirm_info(search_ret, original_title, selection))
            cancel_verify = ttk.Button(search_ret, text="Cancel", command=lambda:cancel_confirm(search_ret))
            confirm_button.grid(column=0, row=i+2, pady =30)
            cancel_verify.grid(column=1, row=i+2, pady=30)
        
    else:
        messagebox.showwarning(title="Warning", message="Invalid database!", icon="warning")

def query_cancel(match_window):
    match_window.destroy()
    
def match_one_movie(curr_title):
    if os.path.exists('movies_db.json')==False:
        messagebox.showwarning(title="Warning", message="no database found!", icon="warning")
    elif tree.focus()!='' or curr_title!='':
        title_chosen = ''
        if curr_title!='':
            title_chosen = curr_title
        else:
            title_chosen = tree.focus()
        if movieDict[title_chosen]['verified']=='x':
            match_window = Toplevel()
            match_window.title("Verify Movie")
            tip_content = 'Some suggestions on editing your search title below:\n'\
                          '-- Delete all useless character. For example\n'\
                          '      X战警：天启.韩版.X-Men.Apocalypse.2016.HD720P.X264.AAC.English.CHS.Mp4Ba ==> X战警：天启\n'\
                          '      X战警：天启.韩版.X-Men.Apocalypse.2016.HD720P.X264.AAC.English.CHS.Mp4Ba ==> X-Men: Apocalypse\n'\
                          '      铜牌巨星.原盘中英字幕.The.Bronze.2015.BD720P.X264.AAC.English.CHS-ENG.Mp4Ba ==> 铜牌巨星\n'\
                          '      铜牌巨星.原盘中英字幕.The.Bronze.2015.BD720P.X264.AAC.English.CHS-ENG.Mp4Ba ==> The Bronze\n'\
                          '      [野鹅敢死队(国英双语)].The.Wild.Geese.1978.BluRay.720p.x264.AC3-CMCT ==> 野鹅敢死队\n'\
                          '      [野鹅敢死队(国英双语)].The.Wild.Geese.1978.BluRay.720p.x264.AC3-CMCT ==> The Wild Geese\n'\
                          '-- If use IMDB as query database, delete all Chinese characters in title or you will get no result.'
            tip_label = ttk.Label(match_window, text=tip_content, width=100, padding=(25, 25, 10, 10), \
                                  font=('Times', '12'), foreground="#339933")
            title_label = ttk.Label(match_window, text='Title:')

            title_variable = StringVar()
            title_variable.set(title_chosen)
            title_entry = ttk.Entry(match_window, textvariable=title_variable, width=60)
            db_label = ttk.Label(match_window, text="Verify Database:")

            query_db = StringVar()
            db_combobox = ttk.Combobox(match_window, values=('IMDB', 'Douban'), textvariable=query_db, width=10)
            query_db.set("Douban")

            submit_button = ttk.Button(match_window, text="Submit", \
                                       command=lambda:query_submit(match_window, title_chosen, title_variable, query_db))
            cancel_button = ttk.Button(match_window, text="Cancel", command=lambda:query_cancel(match_window))

            match_window.geometry('800x420+400+300')
            match_window.resizable(width=False, height=False)
            
            tip_label.grid(column=0, row=0, columnspan=2,sticky=W)
            title_label.grid(column=0, row=1, padx=20, pady=10, sticky=E)
            title_entry.grid(column=1, row=1, sticky=W)
            db_label.grid(column=0, row=2, padx=20, pady=10, sticky=E)
            db_combobox.grid(column=1, row=2, sticky=W)
            submit_button.grid(column=0, row=3, padx=20,pady=15, sticky=E)
            cancel_button.grid(column=1, row=3, padx=20,pady=15, sticky=W)
        else:
            messagebox.showwarning(title="Warning", message="Movie already verified!", icon="warning")
    else:
        messagebox.showwarning(title="Warning", message="no movie selected!", icon="warning")

def match_all_movie(mode):
    if mode=='manual':
        for key in movieDict.keys():
            if movieDict[key]['verified'] == 'x':
                match_one_movie(key)
                
    elif mode=='auto':
        '''
        # create a feedback window letting user know what is going on
        feedback_window = Toplevel()
        feedback_window.title("Verifying movies...")
        curr_title = StringVar()
        curr_title.set("Starting...")
        progress_label = ttk.Label(feedback_window, textvariable=curr_title, width=60, foreground="#ff9900")
        progress_label.grid()
        '''        
        # store list of matched titles
        list_dict = []
        for key in movieDict.keys():
            if movieDict[key]['verified'] == 'x' and movieDict[key]['runtime']!=0:
                # this is the search results page
                # curr_title.set("Processing " + key)
                print("Processing " + key)
                res = requests.get('https://movie.douban.com/subject_search?search_text=' + key)
                doubanSoup = bs4.BeautifulSoup(res.text, "html.parser")
                
                # fetch link
                search_ret = doubanSoup.select('.nbg')
                if len(search_ret) > 6:
                    search_ret = search_ret[0:6]
                # iterate search results and compare the duration
                # if duration difference is less than 2 mins
                # and if only one result left, add it into list_dict
                for tagob in search_ret:
                    tagRegex = re.compile(r'.+href=["|\'](.+?)["|\'].+title=["|\'](.+?)["|\'].+src="(.+?)".+', re.S)
                    mo = tagRegex.search(str(tagob))
                    if mo!=None:
                        link = mo.group(1)
                        html_content = requests.get(link)
                        soup = bs4.BeautifulSoup(html_content.text, "html.parser")
                        ret = soup.select('h1 span')
                        if ret != []:
                            title = ret[0].getText()
                            special_char = ['/', ':', '*', '?', '"', '<', '>', '|']
                            list_str = list(title)
                            
                            # replace invalid chars in file name
                            for i in range(len(list_str)):
                                if list_str[i] in special_char:
                                    list_str[i] = '-'
                            title = "".join(list_str)
                            
                            if title != key and title in movieDict.keys():
                                pass
                            else:
                                if len(search_ret) == 1:
                                    ret_record = {'title_db':title, 'link':link, 'title_query':key}
                                    list_dict.append(ret_record)
                                    break
                                # looking for duration
                                ret = soup.select('#info span[property="v:runtime"]')
                                if ret!=[]:
                                    regex = re.compile(r'^(\d+)')
                                    mo = regex.search(ret[0].getText())
                                    if mo!=None:
                                        length = movieDict[key]['runtime']
                                        time_range = [length - 1, length, length + 1]
                                        # fetch duration from douban
                                        runtime = int(mo.group(1))
                                        # compare duration between db and local file
                                        if runtime in time_range:
                                            ret_record = {'title_db':title, 'link':link, 'title_query':key}
                                            list_dict.append(ret_record)
                                            break
        #feedback_window.destroy()

        if len(list_dict)==0:
            messagebox.showwarning(title="Warning", message="no matches found!", icon="warning")
        else:
            # tracking on/off status of checkbuttons
            list_var = []
            for i in range(len(list_dict)):
                sv = StringVar()
                list_var.append(sv)
                sv.set('on')

            global start_n, end_n, total_n, curr_page, page_num
            start_n = 0
            total_n = len(list_dict)
            page_num = int((total_n-1)/15) + 1
            curr_page = 1
            end_n = total_n
            if end_n > 15:
                end_n = 15

            # create a window that allows user to double-check the matches and submit
            user_confirm_window = Toplevel()
            user_confirm_window.title('Match movies to Douban database')
            # instruction
            instruction_label = ttk.Label(user_confirm_window, text="Check the box when you are sure the match is accurate.")
            instruction_label.grid(column=0, row=0 , columnspan=2, padx=5, pady=20)        

            # all buttons below the frame
            button_frame = ttk.Frame(user_confirm_window)
            button_frame.grid(column=0, row=2, columnspan=2, padx=10, pady=20)
            select_all_button = ttk.Button(button_frame, text="Select all", command=lambda:select_all(list_var))
            select_none_button = ttk.Button(button_frame, text="Select none", command=lambda:select_none(list_var))
            previous_button = ttk.Button(button_frame, text="Previous", command=lambda:previous(user_confirm_window, list_dict,list_var))
            next_button = ttk.Button(button_frame, text="Next", command=lambda:nextpage(user_confirm_window, list_dict,list_var))
            confirm_button = ttk.Button(button_frame, text="Confirm", command=lambda:user_confirm(user_confirm_window, list_var, list_dict))
            cancel_button = ttk.Button(button_frame, text="Cancel", command=lambda:query_cancel(user_confirm_window))
            global curr_p
            curr_p = StringVar()
            curr_p.set(str(curr_page) + '/' + str(page_num))

            curr_page_label = ttk.Label(button_frame, textvariable=curr_p)

            select_all_button.grid(column=0, row=0, padx=15, pady=15)
            select_none_button.grid(column=1, row=0, padx=15, pady=15)
            previous_button.grid(column=2, row=0, padx=15, pady=15)
            next_button.grid(column=3, row=0, padx=15, pady=15)
            confirm_button.grid(column=0, row=1, padx=5, pady=15)
            cancel_button.grid(column=1, row=1, padx=5, pady=15)
            curr_page_label.grid(column=2, row=1, padx=5, pady=15)

            create_match_confirm_window(user_confirm_window, list_dict, list_var)

def previous(user_confirm_window, list_dict,list_var):
    global start_n, end_n, curr_page
    if curr_page > 1:
        curr_page -= 1
        start_n -= 15
        end_n = start_n + 15
    create_match_confirm_window(user_confirm_window, list_dict,list_var)
        
def nextpage(user_confirm_window, list_dict,list_var):
    global start_n, end_n, total_n, curr_page, page_num
    if curr_page < page_num:        
        start_n += 15
        if curr_page==page_num-1:
            end_n = total_n
        else:
            end_n = start_n + 15
        curr_page += 1
    create_match_confirm_window(user_confirm_window, list_dict,list_var)
        
            

def create_match_confirm_window(user_confirm_window, list_dict, list_var):
    global start_n, end_n, total_n, curr_page, page_num, curr_p, frame_ret
    
    if frame_ret!=None:
        frame_ret.destroy()
        
    frame_ret = ttk.Frame(user_confirm_window)
    frame_ret.grid(column=0, row=1, columnspan=2)
    header1_label = ttk.Label(frame_ret, text="Compare title")
    header2_label = ttk.Label(frame_ret, text="Douban link")
    header1_label.grid(column=0, row=0, pady=2)
    header2_label.grid(column=1, row=0, pady=2)
  
        
    for i in range(start_n, end_n):
        two_titles = list_dict[i]['title_db'] + " (douban)\n" + list_dict[i]['title_query'] + " (original)\n"
        cb = ttk.Checkbutton(frame_ret, text=two_titles , variable=list_var[i], onvalue='on', offvalue='off', width=80)
        link_button = ttk.Button(frame_ret, text="link", \
                                 command=lambda:callback2(user_confirm_window, list_dict, 172, 51, 23, start_n))
        
        cb.grid(column=0, row=i-start_n+1, sticky=W, padx=10)
        link_button.grid(column=1, row=i-start_n+1)

    curr_p.set(str(curr_page) + '/' + str(page_num))

def select_all(l):
    global start_n, end_n
    for i in range(start_n, end_n):
        if l[i].get()=='off':
            l[i].set('on')

def select_none(l):
    global start_n, end_n
    for i in range(start_n, end_n):
        if l[i].get()=='on':
            l[i].set('off')


def user_confirm(window, lv, ld):
    window.destroy()
    var_t = StringVar()
    for i in range(len(ld)):
        if lv[i].get() == 'on':            
            var_t.set(ld[i]['link'])
            confirm_info(None, ld[i]['title_query'], var_t)


def callback(window, metadata, bottom, height, interval):
    # bottom is the bottom line y value of first button
    # interval is the distance between two neighbour buttons 
    y = root.winfo_pointery() - window.winfo_y()
    row = 0
    if y >= bottom and (y - bottom)%height == 0:
        row = int((y-bottom)/height)
    else:
        row = int((y-bottom+height-interval)/height)
    webbrowser.open(metadata[row]['link'])

def callback2(window, metadata, bottom, height, interval, i):
    # start_p is the bottom line y value of first button
    # interval_d is the distance of top line between two 
    # neighbour buttons 
    y = root.winfo_pointery() - window.winfo_y()
    print('y: ', y)
    row = 0
    if y >= bottom and (y - bottom)%height == 0:
        row = int((y-bottom)/height)
    else:
        row = int((y-bottom+height-interval)/height)
    print('row: ', row)
    print('i: ', i)
    webbrowser.open(metadata[i + row]['link'])
    

# for modify movie window
def press_ok(window):
    # close modify movie window
    window.destroy()
    global title_temp, title_value, director_value, writers_value, cast_value, year_value,\
           how_long_value, poster_value, trailer_value, storyline_value, genre_value, \
           restriction_value, verified_value, rating_value
    # retrive data from entry and combobox and store them in a list
    alist = [title_temp, title_value.get(), director_value.get(), writers_value.get(), \
             cast_value.get(), year_value.get(), how_long_value.get(), poster_value.get(), \
             trailer_value.get(), storyline_value.get(), genre_value.get(), restriction_value.get(), \
             verified_value.get(), rating_value.get()]

    # updated title is already in database
    if alist[1] != alist[0] and alist[1] in movieDict.keys():  
        messagebox.showwarning(title="Warning", \
                               message="Modified title is already in the database!\nPlease check/correct the title.", \
                               icon="warning")
    # update movie data based on user input
    else:
        folderName = movieDict[alist[0]]['path']
        exten_t = movieDict[alist[0]]['extention']
        size_t = movieDict[alist[0]]['size']
        link = movieDict[alist[0]]['link']
        del movieDict[alist[0]]
        
        verify_t = ''
        if alist[12] == 'Yes':
            verify_t = '√'
        else:
            verify_t = 'x'
        # update dictionary
        record = {'genres': alist[10], 'director':alist[2], 'star':alist[4], 'runtime':int(alist[6]), \
                  'path':folderName, 'poster':alist[7], 'trailer':alist[8], 'restriction':alist[11],\
                  'year':alist[5], 'writers':alist[3], 'storyline':alist[9],'verified':verify_t, \
                  'extention':exten_t, 'size':size_t, 'link':link, 'rating':alist[13]} 
        movieDict[alist[1]] = record

        # update search ret window
        if alist[0] in map_q.keys():
            record['title'] = alist[1]
            list_ret[map_q[alist[0]]] = record
            if alist[0]!=alist[1]:
                map_q[alist[1]] = map_q[alist[0]]
                del map_q[alist[0]]

        # rename the movie file in hard drive
        if alist[1] != alist[0]:
            shutil.move(os.path.join(folderName, alist[0]) + '.' + exten_t, os.path.join(folderName, alist[1]) + '.' + exten_t)

        # wirte update back to json file
        moviesdbFile = open('movies_db.json', 'w')
        moviesdbFile.write(json.dumps(movieDict))
        moviesdbFile.close()

        create_treelistview()

# for modify movie window
def press_cancel(window):
    window.destroy()


def modify_movie():
    # no database
    if os.path.exists('movies_db.json')==False:
        messagebox.showwarning(title="Warning", message="no database found!", icon="warning")
    # valid movie selected
    elif tree.focus()!='':
        global title_temp
        title_temp = tree.focus()
        modify_window = Toplevel()
        modify_window.title('Modify ' + '"' + title_temp + '"' + ' at ' + movieDict[title_temp]['path'])

        # create 11 labels
        titles = ttk.Label(modify_window, text='Title', padding=(15,15,5,5))
        director = ttk.Label(modify_window, text='Director', padding=(15,5,5,5))
        writers = ttk.Label(modify_window, text='Writers', padding=(15,5,5,5))
        cast = ttk.Label(modify_window, text='Cast', padding=(15,5,5,5))
        genre = ttk.Label(modify_window, text='Genre', padding=(15,5,5,5))
        restriction = ttk.Label(modify_window, text='Restriction', padding=(15,5,5,5))
        year= ttk.Label(modify_window, text='Year', padding=(15,5,5,5))
        how_long = ttk.Label(modify_window, text='Runtime (min)', padding=(15,5,5,5))
        poster = ttk.Label(modify_window, text='Poster (url)', padding=(15,5,5,5))
        trailer = ttk.Label(modify_window, text='Trailer (url)', padding=(15,5,5,5))
        storyline = ttk.Label(modify_window, text='Storyline', padding=(15,5,5,5))
        rating = ttk.Label(modify_window, text='Rating', padding=(15,5,5,5))
        verified = ttk.Label(modify_window, text='Verified', padding=(15,5,5,5))
        

        # create 9 entries with initialized value
        global title_value
        title_value = StringVar()
        title_value.set(title_temp)
        e_title = ttk.Entry(modify_window, textvariable=title_value, width=70)
        
        global director_value
        director_value = StringVar()
        director_value.set(movieDict[title_temp]['director'])
        e_director = ttk.Entry(modify_window, textvariable=director_value)

        global writers_value
        writers_value = StringVar()
        writers_value.set(movieDict[title_temp]['writers'])
        e_writers = ttk.Entry(modify_window, textvariable=writers_value, width=30)

        global cast_value
        cast_value = StringVar()
        cast_value.set(movieDict[title_temp]['star'])
        e_cast = ttk.Entry(modify_window, textvariable=cast_value, width=60)

        global year_value
        year_value = StringVar()
        year_value.set(movieDict[title_temp]['year'])
        e_year= ttk.Entry(modify_window, textvariable=year_value, width=10)

        global how_long_value
        how_long_value = StringVar()
        how_long_value.set(movieDict[title_temp]['runtime'])
        e_how_long = ttk.Entry(modify_window, textvariable=how_long_value, width=10)

        global poster_value
        poster_value = StringVar()
        poster_value.set(movieDict[title_temp]['poster'])
        e_poster = ttk.Entry(modify_window, textvariable=poster_value, width=30)

        global trailer_value
        trailer_value = StringVar()
        trailer_value.set(movieDict[title_temp]['trailer'])
        e_trailer = ttk.Entry(modify_window, textvariable=trailer_value, width=30)

        global storyline_value
        storyline_value = StringVar()
        storyline_value.set(movieDict[title_temp]['storyline'])
        e_storyline = ttk.Entry(modify_window, textvariable=storyline_value, width=30)

        global rating_value
        rating_value = StringVar()
        rating_value.set(movieDict[title_temp]['rating'])
        e_rating = ttk.Entry(modify_window, textvariable=rating_value, width=30)

        # 3 combobox for genre, restriction and verified
        global genre_value
        genre_value = StringVar()
        genre_value.set(movieDict[title_temp]['genres'])
        combo_genre = ttk.Combobox(modify_window, textvariable=genre_value, width=10)

        global restriction_value
        restriction_value = StringVar()
        restriction_value.set(movieDict[title_temp]['restriction'])
        combo_restriction = ttk.Combobox(modify_window, textvariable=restriction_value, width=10)

        global verified_value
        verified_value = StringVar()
        if movieDict[title_temp]['verified'] == '√':
            verified_value.set('Yes')
        else:
            verified_value.set('No')
        combo_verified = ttk.Combobox(modify_window, values=('Yes', 'No'), textvariable=verified_value, width=5)

        # 2 buttons: Ok, Cancel
        ok_button = ttk.Button(modify_window, text='Ok', command=lambda:press_ok(modify_window))
        cancel_button = ttk.Button(modify_window, text='Cancel', command=lambda: press_cancel(modify_window))
        

        titles.grid(column=0, row=0, sticky=W)
        director.grid(column=0, row=1, sticky=W)
        writers.grid(column=0, row=2, sticky=W)
        cast.grid(column=0, row=3, sticky=W)
        genre.grid(column=0, row=4, sticky=W)
        restriction.grid(column=0, row=5, sticky=W)
        year.grid(column=0, row=6, sticky=W)
        how_long.grid(column=0, row=7, sticky=W)
        poster.grid(column=0, row=8, sticky=W)
        trailer.grid(column=0, row=9, sticky=W)
        storyline.grid(column=0, row=10, sticky=W)
        rating.grid(column=0, row=11, sticky=W)
        verified.grid(column=0, row=12, sticky=W)

        e_title.grid(column=1, row=0, sticky=W)
        e_director.grid(column=1, row=1, sticky=W)
        e_writers.grid(column=1, row=2, sticky=W)
        e_cast.grid(column=1, row=3, sticky=W)
        e_year.grid(column=1, row=6, sticky=W)
        e_how_long.grid(column=1, row=7, sticky=W)
        e_poster.grid(column=1, row=8, sticky=W)
        e_trailer.grid(column=1, row=9, sticky=W)
        e_storyline.grid(column=1, row=10, sticky=W)
        e_rating.grid(column=1, row=11, sticky=W)

        combo_genre.grid(column=1, row=4, sticky=W)
        combo_restriction.grid(column=1, row=5, sticky=W)
        combo_verified.grid(column=1, row=12, sticky=W)

        ok_button.grid(column=0, row=15, sticky=E, pady=30)
        cancel_button.grid(column=1, row=15)
    else:
        messagebox.showwarning(title="Warning", message="no movie selected!", icon="warning")

def delete_movie():
    if os.path.exists('movies_db.json')==False or tree.focus()=="":
        messagebox.showwarning(title="Warning", message="No movie selected!", icon="warning")
    else:
        result = messagebox.askyesno(message="Are you sure you want to delete " + '"'+ tree.focus() + '" ?', \
                                     title="Delete movie", icon="question")
        if result:
            if tree.focus() in map_q.keys():
                del list_ret[map_q[tree.focus()]]
                del map_q[tree.focus()]
            del movieDict[tree.focus()]
            if len(movieDict)==0:
                os.unlink('movies_db.json')
                tree.grid_remove()
                frame.grid_remove()
                scrollbar.grid_remove()
                root.geometry('500x300+300+300')
                start_frame.grid()
            else:
                moviesdbFile = open('movies_db.json', 'w')
                moviesdbFile.write(json.dumps(movieDict))
                moviesdbFile.close()
                create_treelistview()

def confirm_header():
    global heading_display  
    heading_display = []
    if title_c.get()=='on':
        heading_display.append('title')

    if year_c.get()=='on':
        heading_display.append('year')

    if director_c.get()=='on':
        heading_display.append('director')

    if writers_c.get()=='on':
        heading_display.append('writers')

    if star_c.get()=='on':
        heading_display.append('star')

    if genres_c.get()=='on':
        heading_display.append('genres')

    if runtime_c.get()=='on':
        heading_display.append('runtime')

    if rating_c.get()=='on':
        heading_display.append('rating')

    if size_c.get()=='on':
        heading_display.append('size')

    if extention_c.get()=='on':
        heading_display.append('extention')

    if path_c.get()=='on':
        heading_display.append('path')

    if verified_c.get()=='on':
        heading_display.append('verified')

    create_treelistview()
        

def done_header():
    confirm_header()    
    header.destroy()    


def select_header():
    global header
    header = Toplevel()
    header.title('Select headers')

    global title_c
    title_c = StringVar()
    title = ttk.Checkbutton(header, text='Title', variable=title_c, onvalue='on', offvalue='off') 

    global year_c
    year_c = StringVar()
    year = ttk.Checkbutton(header, text='Year', variable=year_c, onvalue='on', offvalue='off')

    global director_c
    director_c = StringVar()
    director = ttk.Checkbutton(header, text='Director', variable=director_c, onvalue='on', offvalue='off')

    global writers_c
    writers_c = StringVar()
    writers = ttk.Checkbutton(header, text='Writers', variable=writers_c, onvalue='on', offvalue='off')

    global star_c
    star_c = StringVar()
    star = ttk.Checkbutton(header, text='Star', variable=star_c, onvalue='on', offvalue='off')

    global genres_c
    genres_c = StringVar()
    genres = ttk.Checkbutton(header, text='Genre', variable=genres_c, onvalue='on', offvalue='off')

    global runtime_c
    runtime_c = StringVar()
    runtime = ttk.Checkbutton(header, text='Runtime', variable=runtime_c, onvalue='on', offvalue='off')

    global rating_c
    rating_c = StringVar()
    rating = ttk.Checkbutton(header, text='Rating', variable=rating_c, onvalue='on', offvalue='off')

    global size_c
    size_c = StringVar()
    size = ttk.Checkbutton(header, text='Size', variable=size_c, onvalue='on', offvalue='off')

    global extention_c
    extention_c = StringVar()
    extention = ttk.Checkbutton(header, text='Extention', variable=extention_c, onvalue='on', offvalue='off')

    global path_c
    path_c = StringVar()
    path = ttk.Checkbutton(header, text='Path', variable=path_c, onvalue='on', offvalue='off')

    global verified_c
    verified_c = StringVar()
    verified = ttk.Checkbutton(header, text='Verified', variable=verified_c, onvalue='on', offvalue='off')

    ok_button = ttk.Button(header, text="Apply", command=confirm_header)
    cancel_button = ttk.Button(header, text="I'm done!", command=done_header)

    global heading_display
    if 'title' in heading_display:
        title_c.set('on')

    if 'year' in heading_display:
        year_c.set('on')

    if 'director' in heading_display:
        director_c.set('on')

    if 'writers' in heading_display:
        writers_c.set('on')

    if 'star' in heading_display:
        star_c.set('on')

    if 'genres' in heading_display:
        genres_c.set('on')

    if 'runtime' in heading_display:
        runtime_c.set('on')

    if 'rating' in heading_display:
        rating_c.set('on')

    if 'size' in heading_display:
        size_c.set('on')

    if 'extention' in heading_display:
        extention_c.set('on')

    if 'path' in heading_display:
        path_c.set('on')

    if 'verified' in heading_display:
        verified_c.set('on')    

    title.grid(column=0, row=0, padx = 10, pady = 10, sticky=W)
    year.grid(column=0, row=1, padx = 10, pady = 10, sticky=W)
    director.grid(column=0, row=2, padx = 10, pady = 10, sticky=W)
    writers.grid(column=0, row=3, padx = 10, pady = 10, sticky=W)
    star.grid(column=0, row=4, padx = 10, pady = 10, sticky=W)
    genres.grid(column=0, row=5, padx = 10, pady = 10, sticky=W)
    runtime.grid(column=1, row=0, padx = 10, pady = 10, sticky=W)
    rating.grid(column=1, row=1, padx = 10, pady = 10, sticky=W)
    size.grid(column=1, row=2, padx = 10, pady = 10, sticky=W)
    extention.grid(column=1, row=3, padx = 10, pady = 10, sticky=W)
    path.grid(column=1, row=4, padx = 10, pady = 10, sticky=W)
    verified.grid(column=1, row=5, padx = 10, pady = 10, sticky=W)

    ok_button.grid(column=0, row=12, padx = 10, pady=40)
    cancel_button.grid(column=1, row=12, padx=10, pady=40)


def search_submit():
    global list_ret, keywords, whole_db, newlist, map_q
        
    # close search movie window   
    search_window.destroy()    
    # store index of newlist that matches the search keywords    
    index_ret = []
    criteria=[]
    for i in range(len(newlist)):    
        index_ret.append(i)

    if title_search.get() !='':
        list_temp = []
        criteria.append('Title: ' + title_search.get())
        mRegex = re.compile(r'.*' + re.escape(title_search.get()) + r'.*', re.I | re.S)
        for i in index_ret:
            if mRegex.search(newlist[i]['title']) != None:
                list_temp.append(i)    
        index_ret = list_temp

    if genre_search.get() !='':
        list_temp = []
        criteria.append('Genre: ' + genre_search.get())
        mRegex = re.compile(r'.*' + re.escape(genre_search.get()) + r'.*', re.I | re.S)
        for i in index_ret:
            if mRegex.search(newlist[i]['genres']) != None:
                list_temp.append(i)    
        index_ret = list_temp

    if director_search.get() !='':
        list_temp = []
        criteria.append('Director: ' + director_search.get())
        mRegex = re.compile(r'.*' + re.escape(director_search.get()) + r'.*', re.I | re.S)
        for i in index_ret:
            if mRegex.search(newlist[i]['director']) != None:
                list_temp.append(i)    
        index_ret = list_temp

    if star_search.get() !='':
        list_temp = []
        criteria.append('Actor: ' + star_search.get())
        mRegex = re.compile(r'.*' + re.escape(star_search.get()) + r'.*', re.I | re.S)
        for i in index_ret:
            if mRegex.search(newlist[i]['star']) != None:
                list_temp.append(i)    
        index_ret = list_temp

    if year_search.get() !='':
        list_temp = []
        criteria.append('Year: ' + year_search.get())
        mRegex = re.compile(r'.*' + re.escape(year_search.get()) + r'.*', re.I | re.S)
        for i in index_ret:
            if mRegex.search(newlist[i]['year']) != None:
                list_temp.append(i)    
        index_ret = list_temp

    if writer_search.get() !='':
        list_temp = []
        criteria.append('Writer: ' + writer_search.get())
        mRegex = re.compile(r'.*' + re.escape(writer_search.get()) + r'.*', re.I | re.S)
        for i in index_ret:
            if mRegex.search(newlist[i]['writers']) != None:
                list_temp.append(i)    
        index_ret = list_temp

    if rating_search.get() !='':
        list_temp = []
        criteria.append('Rating: ' + rating_search.get())    
        score = rating_search.get()
        if len(score)==1:            
            score += '.0/10'    
        for i in index_ret:
            if newlist[i]['rating'] >= score:
                list_temp.append(i)    
        index_ret = list_temp

    if verify_search.get() !='':
        list_temp = []
        criteria.append('Verified: ' + verify_search.get())
        for i in index_ret:
            if newlist[i]['verified'] == verify_search.get():
                list_temp.append(i)    
        index_ret = list_temp

    # list_ret stores a list of dictionary after filtering by search keywords
    list_ret = []
    map_q = {}
    for i in index_ret:        
        list_ret.append(newlist[i])
        map_q[newlist[i]['title']] = len(list_ret)-1


    keywords = criteria
    whole_db = False
    create_treelistview()
    

def cancel_search():
    search_window.destroy()

def validateRating():
    global rating_search
    ratings = rating_search.get()
    if ratings=='':
        return True
    if len(ratings) > 3:
        return False
    try:
        r = float(ratings)
        if r > 10.0 or r < 0.0:
            return False
        return True
    except ValueError:
        return False
    
def inputwarning():
    messagebox.showwarning(title="Warning", message="Invalid rating input!", icon="warning")


def typeahead(event):
    global director_search_combobox, star_search_combobox, writer_search_combobox
    global director_search, star_search, writer_search
    global director_collection, actor_collection, writer_collection
    global director_t, star_t, writer_t, d_str, s_str, w_str


    if director_search_combobox!=None:
        director_search_combobox.destroy()

    if star_search_combobox!=None:
        star_search_combobox.destroy()    
    
    if writer_search_combobox!=None:
        writer_search_combobox.destroy()
        
    if director_search.get() != d_str:
        d_str = director_search.get()
        director_t = []
        regex = re.compile(r'^' + d_str + r'.*', re.I | re.S)
        for d in director_collection:
            if regex.search(d)!=None:
                director_t.append(d)
    
    if star_search.get() != s_str:
        s_str = star_search.get()
        star_t = []
        regex = re.compile(r'^' + s_str + r'.*', re.I | re.S)
        for d in actor_collection:
            if regex.search(d)!=None:
                star_t.append(d)


    if writer_search.get() != w_str:
        w_str = writer_search.get()
        writer_t = []
        regex = re.compile(r'^' + w_str + r'.*', re.I | re.S)
        for d in writer_collection:
            if regex.search(d)!=None:
                writer_t.append(d)


    director_search_combobox = ttk.Combobox(search_window, textvariable=director_search, values=tuple(director_t))
    director_search_combobox.bind('<FocusOut>', typeahead)

    star_search_combobox = ttk.Combobox(search_window, textvariable=star_search, values=tuple(star_t))
    star_search_combobox.bind('<FocusOut>', typeahead)

    writer_search_combobox = ttk.Combobox(search_window, textvariable=writer_search, values=tuple(writer_t))
    writer_search_combobox.bind('<FocusOut>', typeahead)
    
    director_search_combobox.grid(column=1, row=3, sticky=W)
    star_search_combobox.grid(column=1, row=4, sticky=W)
    writer_search_combobox.grid(column=1, row=6, sticky=W)

def search():
    # no database
    if os.path.exists('movies_db.json')==False:
        messagebox.showwarning(title="Warning", message="no database found!", icon="warning")
    else:
        # extrac info for keys
        global director_collection, actor_collection, writer_collection, director_t, star_t, writer_t
        genre_collection = []
        director_collection = []
        actor_collection = []
        year_collection = []
        writer_collection = []

        for i in range(len(newlist)):    
            genre_list = newlist[i]['genres'].split('/')
            for g in genre_list:
                if g!= '' and g not in genre_collection:
                    genre_collection.append(g)

            director_list = newlist[i]['director'].split('/')
            for d in director_list:
                if d!='' and d not in director_collection:    
                    director_collection.append(d)

            actor_list = newlist[i]['star'].split('/')
            for a in actor_list:
                if a !='' and a not in actor_collection:
                    actor_collection.append(a)

            year = newlist[i]['year']
            if  year!= 'NA' and year not in year_collection:
                year_collection.append(year)

            writer_list = newlist[i]['writers'].split('/')
            for w in writer_list:
                if w !='' and w not in writer_collection:
                    writer_collection.append(w)


        global search_window, director_search_combobox, star_search_combobox, writer_search_combobox
        director_search_combobox = None
        star_search_combobox = None
        writer_search_combobox = None

        global d_str, s_str, w_str
        d_str = ''
        s_str = ''
        w_str = ''
        
        search_window = Toplevel()
        search_window.title('Search moives')
        tip = "Type your keywords or select from a drop-down menu.\n"\
              "Leave it blank if you don't want it to be a keyword."
        tip_label = ttk.Label(search_window, text=tip, padding=(15,5,0,5), width=60, wraplength=600)
        
        title_search_label = ttk.Label(search_window, text="Title:")
        global title_search
        title_search = StringVar()
        title_search_entry = ttk.Entry(search_window, width = 50, textvariable=title_search, takefocus=True)
 
        
        genre_search_label = ttk.Label(search_window, text="Genre:")
        global genre_search
        genre_search = StringVar()
        genre_collection.sort()
        genre_search_combobox = ttk.Combobox(search_window, width = 10, textvariable=genre_search, values=tuple(genre_collection))

        director_search_label = ttk.Label(search_window, text="Director:")
        global director_search
        director_search = StringVar()
        director_collection.sort()
        

        star_search_label = ttk.Label(search_window, text="Star:")
        global star_search
        star_search = StringVar()
        actor_collection.sort()
        

        year_search_label = ttk.Label(search_window, text="Year:")
        global year_search
        year_search = StringVar()
        year_collection.sort()
        year_search_combobox = ttk.Combobox(search_window, width = 10, textvariable=year_search, values=tuple(year_collection))

        writer_search_label = ttk.Label(search_window, text="Writer:")
        global writer_search
        writer_search = StringVar()
        writer_collection.sort()
        

        rating_search_label = ttk.Label(search_window, text="Rating (>=):")
        global rating_search
        rating_search = StringVar()
        okCommand = search_window.register(validateRating)
        rating_search_entry = ttk.Entry(search_window, width = 10, textvariable=rating_search, validate='focusout', \
                                        validatecommand=okCommand, invalidcommand=inputwarning)
        

        verify_search_label = ttk.Label(search_window, text="Verified:")
        global verify_search
        verify_search = StringVar()
        verify_search_combobox = ttk.Combobox(search_window, width = 10, textvariable=verify_search, values=('√', 'x'))

        submit_search_button = ttk.Button(search_window, text="Submit", command=search_submit)
        cancel_search_button = ttk.Button(search_window, text="Cancel", command=cancel_search)

        search_window.geometry('690x450')
        search_window.resizable(width=False, height=False)
        search_window
        tip_label.grid(column=0, row=0, padx=20, pady=20, columnspan=2)
        
        title_search_label.grid(column=0, row=1, padx=20,sticky=E)
        title_search_entry.grid(column=1, row=1, sticky=W)

        genre_search_label.grid(column=0, row=2, padx=20, sticky=E)
        genre_search_combobox.grid(column=1, row=2, sticky=W)

        director_search_label.grid(column=0, row=3, padx=20,sticky=E)
        

        star_search_label.grid(column=0, row=4, padx=20,sticky=E)
        

        year_search_label.grid(column=0, row=5, padx=20,sticky=E)
        year_search_combobox.grid(column=1, row=5, sticky=W)

        writer_search_label.grid(column=0, row=6, padx=20,sticky=E)
        

        rating_search_label.grid(column=0, row=7, padx=20,sticky=E)
        rating_search_entry.grid(column=1, row=7, sticky=W)
        
        verify_search_label.grid(column=0, row=8, padx=20,sticky=E)
        verify_search_combobox.grid(column=1, row=8, sticky=W)

        submit_search_button.grid(column=0, row=9, padx=20, pady=30, sticky=E)
        cancel_search_button.grid(column=1, row=9, padx=20, pady=30, sticky=W)

        director_t = director_collection
        star_t = actor_collection
        writer_t = writer_collection
        
        typeahead('')


        

root = Tk()

# Without it, each of your menus (on Windows and X11) will start with what looks like a dashed line,
# and allows you to "tear off" the menu so it appears in its own window. You really don't want that there.
root.option_add('*tearOff', FALSE)
root.title('Local Movie Management')
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)


# menubar is the menu of root, which seems a menubutton for toplevel window
menubar = Menu(root)

root['menu'] = menubar

menu_file = Menu(menubar)
menu_edit = Menu(menubar)
menu_verify = Menu(menubar)
menu_search = Menu(menubar)
menu_view = Menu(menubar)
menu_help = Menu(menubar)
menubar.add_cascade(menu=menu_file, label="File")
menubar.add_cascade(menu=menu_edit, label="Edit")
menubar.add_cascade(menu=menu_verify, label="Verify")
menubar.add_cascade(menu=menu_search, label="Search")
menubar.add_cascade(menu=menu_view, label="View")
menubar.add_cascade(menu=menu_help, label="Help")

menu_file.add_command(label="Scan a directory", command=scan_directory)
menu_file.add_command(label="Add a movie", command=add_movie)
menu_file.add_command(label="Movie detail", command=lambda:detail(tree))
menu_file.add_command(label="Database Stat", command=get_stat)
menu_file.add_command(label="Exit", command=exit_program)

menu_edit.add_command(label="Modify a movie", command=modify_movie)
menu_edit.add_command(label="Delete a movie", command=delete_movie)
menu_edit.add_command(label="Delete database", command=delete_db)

menu_verify.add_command(label="Verify a movie manually", command=lambda:match_one_movie(''))
menu_verify.add_command(label="Verify movies manually", command=lambda:match_all_movie('manual'))
menu_verify.add_command(label="Verify movies automatically", command=lambda:match_all_movie('auto'))

menu_search.add_command(label="Search", command=search)

menu_view.add_command(label="Select header", command=select_header)

menu_help.add_command(label="ReadMe", command=readme)
menu_help.add_command(label="About", command=about)



# create some styles for label, button
s = ttk.Style()
s.configure('TLabel', font=('Cambria', '16'))
s.configure('small.TLabel', font=('Cambria', '10'))
s.configure('TButton', foreground='green', font=('Helvetica', '12', 'bold'), borderwidth=2, relief="sunken")

# frequently used video format
video_format = ['3g2', '3gp', 'amv', 'asf', 'avi', 'drc', 'f4a', 'f4b', 'f4p', 'f4v', 'flv',\
                'gif', 'gifv', 'm2v', 'm4p', 'm4v', 'mkv', 'mng', 'mov', 'mp2', 'mp4', 'mpe', \
                'mpeg', 'mpg', 'mpv', 'mxf', 'nsv', 'ogg', 'ogv', 'qt', 'rm', 'rmvb', 'roq', \
                'svi', 'vob', 'webm', 'wmv', 'yuv']

start_frame = ttk.Frame(root)
label_content = StringVar()
label = ttk.Label(start_frame, textvariable=label_content)
label_content.set("You haven't created your own movie database yet!\nCreate one now")
scan_button = ttk.Button(start_frame, text="Scan a directory", command=scan_directory)

# several global variables to be used by different functions
width = 1500 # for root window
height = 900 # for root window
tree = None
frame_ret = None
movieDict = {}

# for sorted list by any attribute from json file
newlist = []
list_ret = []
map_q = {} # list_ret index to movieDict title

# which heading should be displayed in treeviewlist
heading_display = ['title', 'genres', 'rating', 'director']

# default sorting key
sorted_by = 'title'

# search keywords
keywords = ''

# whether reverse the order of sorted_by when clicking header
is_reverse = False

# whole database or just search result
whole_db = True

if (os.path.exists('movies_db.json') == False):
    root.geometry('500x300')
    start_frame.grid()
    label.grid()
    scan_button.grid()
else:
    create_treelistview()

root.mainloop()
