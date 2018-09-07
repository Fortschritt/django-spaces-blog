// set textareas ckeditor should attach to
CKEDITOR.replaceClass='CKEditor';

var activateMarkdown = function() {
    CKEDITOR.instances[contentSelector].setMode('markdown')
};

var activateWysiwyg = function() {
    CKEDITOR.instances[contentSelector].setMode('wysiwyg')
};

var contentSelector = 'id_content'

/*
	CKEditor expects html as input, so we frontrun it a bit
	by converting the textarea markdown content first
*/

var initialMarkdown = $('#'+contentSelector).html()
$.getScript(CKEDITOR.basePath + 'plugins/markdown/js/marked.js', function() {
	$('#'+contentSelector).html(marked(initialMarkdown, {langPrefix: 'language-'}));
});

/*
  The CKEditor plugin lazyloads the markdown converter on demand.
  We explicitly load all scripts now to ensure markdown conversion is
  complete on page save.
*/
CKEDITOR.on('instanceCreated', function() {
	CKEDITOR.scriptLoader.load(CKEDITOR.basePath + 'plugins/markdown/js/to-markdown.js')
	CKEDITOR.document.appendStyleSheet(CKEDITOR.basePath + 'plugins/markdown/css/codemirror.min.css');
	CKEDITOR.scriptLoader.load(CKEDITOR.basePath + 'plugins/markdown/js/codemirror-gfm-min.js')
});


var prepareSave = function(selector) {
	$(selector).on('click', function(ev) {
        activateMarkdown();
    });
}

// create article
if ($('#createForm').length) {

	var formSelector = 'createForm';
    var saveButtonSelector = '#'+formSelector+' button[type="submit"]'
	prepareSave(saveButtonSelector);
}

// edit article
if ($('#editForm').length) {
	var formSelector = 'editForm';
	var saveButtonSelector = '#'+formSelector+' button[type="submit"]'
	prepareSave(saveButtonSelector);
	
}