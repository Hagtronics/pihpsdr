// Written By Steve Hageman
// No License, free to use

#include <gtk/gtk.h>
#include <semaphore.h>
#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "notch_menu.h"
#include "band.h"
#include "client_server.h"
#include "message.h"
#include "new_menu.h"
#include "new_protocol.h"
#include "radio.h"
#ifdef SOAPYSDR
  #include "soapy_protocol.h"
#endif

static GtkWidget *dialog = NULL;

// Notch is initially off
static gboolean notch_state = FALSE;

static void cleanup() {
  if (dialog != NULL) {
    GtkWidget *tmp = dialog;
    dialog = NULL;
    gtk_widget_destroy(tmp);
    sub_menu = NULL;
    active_menu  = NO_MENU;
    radio_save_state();
  }
}

static gboolean close_cb () {
  cleanup();
  return TRUE;
}

static void notch_cb(GtkComboBox *widget, gpointer data) {
  notch_state = gtk_toggle_button_get_active(GTK_TOGGLE_BUTTON(widget));
  soapy_protocol_set_rf_notch(active_receiver, notch_state);
}


void notch_t_menu(GtkWidget *parent) {
  dialog = gtk_dialog_new();
  gtk_window_set_transient_for(GTK_WINDOW(dialog), GTK_WINDOW(parent));
  char title[64];

  snprintf(title, sizeof(title), "piHPSDR - Notch");
  GtkWidget *headerbar = gtk_header_bar_new();
  gtk_window_set_titlebar(GTK_WINDOW(dialog), headerbar);
  gtk_header_bar_set_show_close_button(GTK_HEADER_BAR(headerbar), TRUE);
  gtk_header_bar_set_title(GTK_HEADER_BAR(headerbar), title);
  g_signal_connect (dialog, "delete_event", G_CALLBACK (close_cb), NULL);
  g_signal_connect (dialog, "destroy", G_CALLBACK (close_cb), NULL);
  GtkWidget *content = gtk_dialog_get_content_area(GTK_DIALOG(dialog));
  GtkWidget *grid = gtk_grid_new();
  gtk_grid_set_column_spacing (GTK_GRID(grid), 10);
  gtk_grid_set_row_homogeneous(GTK_GRID(grid), TRUE);
  gtk_grid_set_column_homogeneous(GTK_GRID(grid), FALSE);
  GtkWidget *close_b = gtk_button_new_with_label("Close");
  gtk_widget_set_name(close_b, "close_button");
  g_signal_connect (close_b, "button_press_event", G_CALLBACK(close_cb), NULL);
  gtk_grid_attach(GTK_GRID(grid), close_b, 0, 0, 1, 1);
  int row = 1;

  GtkWidget *notch_b = gtk_check_button_new_with_label("Enable MW/FM Notch");
  gtk_widget_set_name(notch_b, "boldlabel");
  gtk_toggle_button_set_active (GTK_TOGGLE_BUTTON (notch_b), notch_state);
  gtk_grid_attach(GTK_GRID(grid), notch_b, 0, row, 1, 1);
  g_signal_connect(notch_b, "toggled", G_CALLBACK(notch_cb), NULL);

  gtk_container_add(GTK_CONTAINER(content), grid);
  sub_menu = dialog;
  gtk_widget_show_all(dialog);

}
