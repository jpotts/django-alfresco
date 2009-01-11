/**
 * jquery.overlay 0.14. Overlay HTML with eyecandy.
 * 
 * http://flowplayer.org/tools/overlay.html
 *
 * Copyright (c) 2008 Tero Piirainen (support@flowplayer.org)
 *
 * Released under the MIT License:
 * http://www.opensource.org/licenses/mit-license.php
 * 
 * >> Basically you can do anything you want but leave this header as is <<
 *
 * Since  : 0.01 - 03/11/2008
 * Version: 0.14 - Thu Nov 06 2008 12:20:24 GMT-0000 (GMT+00:00)
 */ 
(function($) { 
		
	function Overlay(el, params, evt) {
		
		var self = this;
		
		// setup options
		var opts = { 
			speed:500,
			top:100,
			close: null,
			
			onBeforeLoad: null, 
			onLoad: null, 
			onClose: null,
			
			closeOnClick: true
		};
		
		if (typeof params == 'function') {
			params = {onLoad: params};	
		}
		
		$.extend(opts, params); 
		
		// setup content
		var content = $(el.attr("rel"));
		
		if (!content.length) {			
			alert("Cannot find element: " + el.attr("rel") + ", missing \"#\" in rel- attribute?");
			return;
		}		
		
		// one instance visible at once
		if (content.is(":visible")) {
			return;	
		}
		
		
		// close button
		if (!opts.close) {
			content.prepend('<div class="close"></div>');
			opts.close = "div.close";
		} 
		
		var closeButton = content.find(opts.close);
		
		closeButton.one("click.overlay", function() { 
			close();  
		});
				
		
		// setup growing image		
		var width = content.outerWidth({margin:true});		
		var img = $("#_overlayImage");
		
		if (!img.length) {
			img = $("<img id='_overlayImage'>");
			img.css({border:0,position:'absolute'}).width(width).hide(); 
			$('body').append(img);  				
		}
		
		var bg = content.attr("bg");
		
		if (!bg) {
			bg = content.css("backgroundImage");
			bg = bg.substring(bg.indexOf("(") + 1, bg.indexOf(")"));
			content.attr("bg", bg); 
			content.css("backgroundImage", "none");
		}		
		
		// replace hyphens so that Opera works
		img.attr("src", bg.replace(/\"/g, "")); 
		
		function fireEvent(evt) {
			var fn = opts[evt];
			if (fn) {
				
				try {  
					return fn.call(img, content, el, closeButton);
					
				} catch (error) {
					alert("Error calling overlay::" + evt + ", " + error);
					return false;
				} 					
			}
			return true;			
		}
		
		
		// top & left
		var w = $(window); 
		var top = w.scrollTop() + opts.top; 	
		var left = w.scrollLeft() + Math.max((w.width() - img.width()) / 2, 0);		
		
		if (fireEvent("onBeforeLoad") === false) {
			return;	
		}
		
		// animate image and expose content over it
		img.css({top:evt.pageY, left:evt.pageX, width:0}).show();
		
		img.animate({top:top, left:left, width:width}, opts.speed, function() { 

			content.css({
				position:'absolute', 
				top:top, 
				left:left
				
			}).fadeIn("fast", function() { 
				
				fireEvent("onLoad");
				
				var z = img.css("zIndex");
				if (z == 'auto') z = 0;
				closeButton.add(content).css("zIndex", ++z);	
				
				// when window is clicked outside overlay, we close
				if (opts.closeOnClick) {					
					w.bind("click.overlay", function(evt) {
						var target = $(evt.target);
						if (target.attr("id") == '_overlayImage') { return; }
						if (target.attr("bg")) { return; }
						if (target.parents("[bg]").length) { return; }					
						close(); 
					});						
				}
				
				
			});
			
		});				
		
		// close action
		function close() {
			
			if (fireEvent("onClose") === false) {
				return;	
			}
			
			if (img.is(":visible")) {
				img.hide();
				content.hide();		
				if (opts.closeOnClick) {
					w.unbind("click.overlay");
				}
				w.unbind("keypress.overlay");
			} 
		}		
		
		// keyboard::escape
		w.bind("keypress.overlay", function(evt) {
			if (evt.keyCode == 27) {
				close();	
			}
		});		

	
		$.overlayClose = function() {
			close();	
		};
	}
	
	// jQuery plugin initialization
	$.fn.overlay = function(params) {   
			
		this.bind("click.overlay", function(e) {
			var temp =  new Overlay($(this), params, e);
			return e.preventDefault();
		}); 
		
		return this; 
	}; 
	
})(jQuery);

