/* addEventLitsener Polyfill */
(function(win, doc){
	if(win.addEventListener)return;

	function docHijack(p){var old = doc[p];doc[p] = function(v){return addListen(old(v))}}
	function addEvent(on, fn, self){
		return (self = this).attachEvent('on' + on, function(e){
			var e = e || win.event;
			e.preventDefault  = e.preventDefault  || function(){e.returnValue = false}
			e.stopPropagation = e.stopPropagation || function(){e.cancelBubble = true}
			fn.call(self, e);
		});
	}
	function addListen(obj, i){
		if(i = obj.length)while(i--)obj[i].addEventListener = addEvent;
		else obj.addEventListener = addEvent;
		return obj;
	}

	addListen([doc, win]);
	if('Element' in win)win.Element.prototype.addEventListener = addEvent;			//IE8
	else{		//IE < 8
		doc.attachEvent('onreadystatechange', function(){addListen(doc.all)});		//Make sure we also init at domReady
		docHijack('getElementsByTagName');
		docHijack('getElementById');
		docHijack('createElement');
		addListen(doc.all);	
	}
})(window, document);

var menuData = [
    'Organ',
    'Age',
	'Sex',
    'Title',
    'Content',
    'Category',
    'SubCategory',
    'Date',
    'Discussant\'spresentation',
    'Floor diagnosis',
    'Submitter\'s Presentation',
	'Submitter'
];
var categoryData = [
'Alimentary tract &amp; Associated organs',	
'Bone &amp; Joint',
'Breast',
'CNS',
'PNS &amp; Muscles',
'Endocrine System',		
'Female genital tract',				
'Head &amp; Neck',
'Hematopoietic and Lymphatic system',					
'Intra-thoracic organs and Blood vessels',	
'Skin',
'Soft tissues',			
'Urinary tract &amp; Male genital system'
]
/* addEventLitsener Polyfill */
/*

var tempSlideData = {
    organ:'Lung',
    age:64,
    title:'Test...........',
    content:'strategies, they’ve helped optimize the allocation of resources to fight the spread of infection. Algorithms have even detected preliminary signs of an outbreak well before it came to human pathologists’ attention.In a study back in 2014, investigators used statistical modeling to evaluate the testing and treatment of HIV in the U.K. and locate people living with the virus who weren’t aware of their disease status. The team found that — even without behavioral changes on the part of people living with HIV — their approach could reduce new infections by 5%.',
    slideList:[
        {
            filename:'a',
            ext:'svs',
            thumb:'/imgs/thumbs/slide_1.JPG'
        },
        {
            filename:'a',
            ext:'svs',
            thumb:'/imgs/thumbs/slide_1.JPG'
        },
        {
            filename:'a',
            ext:'svs',
            thumb:'/imgs/thumbs/slide_1.JPG'
        },
        {
            filename:'a',
            ext:'svs',
            thumb:'/imgs/thumbs/slide_1.JPG'
        },
        {
            filename:'a',
            ext:'svs',
            thumb:'/imgs/thumbs/slide_1.JPG'
        },
        {
            filename:'a',
            ext:'svs',
            thumb:'/imgs/thumbs/slide_1.JPG'
        },
        {
            filename:'a',
            ext:'svs',
            thumb:'/imgs/thumbs/slide_1.JPG'
        }
    ],
    fileList:[
        {
            filename:'a',
            ext:'hwp'
        },
        {
            filename:'a',
            ext:'pdf'
        },
        {
            filename:'a',
            ext:'doc'
        }
    ],
    replyList:[{
        from:'anonymous',
        text:'strategies, they’ve helped optimize the allocation of resources to fight the spread of infection. Algorithms have even detected preliminary signs of an outbreak well before it came to human pathologists’ attention.In a study back in 2014, investigators used statistical modeling to evaluate the testing and treatment of HIV in the U.K. and locate people living with the virus who weren’t aware of their disease status. The team found that — even without behavioral changes on the part of people living with HIV — their approach could reduce new infections by 5%.',
        
    },{
        from:'anonymous',
        text:'strategies, they’ve helped optimize the allocation of resources to fight the spread of infection. Algorithms have even detected preliminary signs of an outbreak well before it came to human pathologists’ attention.In a study back in 2014, investigators used statistical modeling to evaluate the testing and treatment of HIV in the U.K. and locate people living with the virus who weren’t aware of their disease status. The team found that — even without behavioral changes on the part of people living with HIV — their approach could reduce new infections by 5%.',
        
    },{
        from:'anonymous',
        text:'strategies, they’ve helped optimize the allocation of resources to fight the spread of infection. Algorithms have even detected preliminary signs of an outbreak well before it came to human pathologists’ attention.In a study back in 2014, investigators used statistical modeling to evaluate the testing and treatment of HIV in the U.K. and locate people living with the virus who weren’t aware of their disease status. The team found that — even without behavioral changes on the part of people living with HIV — their approach could reduce new infections by 5%.',
        
    },{
        from:'anonymous',
        text:'strategies, they’ve helped optimize the allocation of resources to fight the spread of infection. Algorithms have even detected preliminary signs of an outbreak well before it came to human pathologists’ attention.In a study back in 2014, investigators used statistical modeling to evaluate the testing and treatment of HIV in the U.K. and locate people living with the virus who weren’t aware of their disease status. The team found that — even without behavioral changes on the part of people living with HIV — their approach could reduce new infections by 5%.',
        
    },{
        from:'anonymous',
        text:'strategies, they’ve helped optimize the allocation of resources to fight the spread of infection. Algorithms have even detected preliminary signs of an outbreak well before it came to human pathologists’ attention.In a study back in 2014, investigators used statistical modeling to evaluate the testing and treatment of HIV in the U.K. and locate people living with the virus who weren’t aware of their disease status. The team found that — even without behavioral changes on the part of people living with HIV — their approach could reduce new infections by 5%.',
        
    }]
}*/
window.addEventListener('DOMContentLoaded',function(){
    console.log(monthlyInfo)
	/*
    var menuData = [
    'Organ',
    'Age',
	'Sex',
    'Title',
    'Content',
    'Category',
    'SubCategory',
    'Date',
	'Discussant',
	'Submitter'
	];*/
    
   
    Object.keys(monthlyInfo).map(function(kv,i){
        var elem = document.querySelector('[rel=js-info-data-'+kv+']');
        console.log('[rel=js-info-data-'+kv+']')
        if(elem){
            if(kv==='strCategory'){
                elem.innerHTML = categoryData[monthlyInfo[kv]];
            }else{
                elem.innerHTML = monthlyInfo[kv];
            }
            
        }
        
    });
    document.querySelector('div[rel=js-image-info]').addEventListener('click',function(){
        
        var infoBox = document.querySelector('div[rel=js-image-infobox]');
        var infoBoxWidth = +getComputedStyle(infoBox,null)['width'].slice(0,-2);

        if(0===infoBoxWidth){  
            infoBox.style.width= '30em';
            infoBox.style.visibility = 'visible';
            setTimeout(function(){
                infoBox.firstElementChild.style.visibility = 'visible';
            },1000);
        }else{
            infoBox.firstElementChild.style.visibility = 'hidden';
            infoBox.style.width= '0em';
            infoBox.style.visibility = 'hidden';
        }
        
    });
    
    
});
