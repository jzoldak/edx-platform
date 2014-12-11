/**
 * View for the "make payment" step of the payment/verification flow.
 */
var edx = edx || {};

(function( $, _, gettext ) {
    'use strict';

    edx.verify_student = edx.verify_student || {};

    edx.verify_student.MakePaymentStepView = edx.verify_student.StepView.extend({

        postRender: function() {
            // Render requirements
            new edx.verify_student.RequirementsView({
                el: $( '.requirements-container', this.el ),
                requirements: this.stepData.requirements
            }).render();

            // Enable the payment button once an amount is chosen
            $( "input[name='contribution']" ).on( 'click', _.bind( this.enablePaymentButton, this ) );

            // Handle payment submission
            $( "#pay_button" ).on( 'click', _.bind( this.createOrder, this ) );
        },

        enablePaymentButton: function() {
            $("#pay_button").removeClass("is-disabled");
        },

        createOrder: function() {
            var paymentAmount = this.getPaymentAmount(),
                postData = {
                    'contribution': paymentAmount,
                    'course_id': this.stepData.courseKey,
                };

            // Disable the payment button to prevent multiple submissions
            $("#pay_button").addClass("is-disabled");

            // Create the order for the amount
            $.ajax({
                url: '/verify_student/create_order/',
                type: 'POST',
                headers: {
                    'X-CSRFToken': $.cookie('csrftoken')
                },
                data: postData,
                context: this,
                success: this.handleCreateOrderResponse,
                error: this.handleCreateOrderError
            });

        },

        handleCreateOrderResponse: function( paymentParams ) {
            // At this point, the order has been created on the server,
            // and we've received signed payment parameters.
            // We need to dynamically construct a form using
            // these parameters, then submit it to the payment processor.
            // This will send the user to a hosted order page,
            // where she can enter credit card information.
            var form = $( "#payment-processor-form" );

            $( "input", form ).remove();

            form.attr( "action", this.stepData.purchaseEndpoint );
            form.attr( "method", "POST" );

            _.each( paymentParams, function( value, key ) {
                $("<input>").attr({
                    type: "hidden",
                    name: key,
                    value: value
                }).appendTo(form);
            });

            form.submit();
        },

        handleCreateOrderError: function( xhr ) {
            if ( xhr.status === 400 ) {
                this.errorModel.set({
                    errorTitle: gettext( 'Could not submit order' ),
                    errorMsg: xhr.responseText,
                    shown: true
                });
            } else {
                this.errorModel.set({
                    errorTitle: gettext( 'Could not submit order' ),
                    errorMsg: gettext( 'An unexpected error occurred.  Please try again' ),
                    shown: true
                });
            }

            // Re-enable the button so the user can re-try
            $( "#payment-processor-form" ).removeClass("is-disabled");
        },

        getPaymentAmount: function() {
            var contributionInput = $("input[name='contribution']:checked", this.el);

            if ( contributionInput.attr('id') === 'contribution-other' ) {
                return $( "input[name='contribution-other-amt']", this.el ).val();
            } else {
                return contributionInput.val();
            }
        }

    });

})( jQuery, _, gettext );