# Generated by Django 2.1.3 on 2019-04-01 07:58

from django.db import migrations, models
import django.db.models.deletion
import djongo.models.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('applications', '0003_auto_20190401_0758'),
        ('services', '0001_initial'),
        ('system', '0001_initial'),
        ('gui', '0001_initial'),
        ('darwin', '0001_initial'),
        ('toolkit', '0002_auto_20190401_0758'),
        ('workflow', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='frontend',
            name='backend',
            field=models.ManyToManyField(through='workflow.Workflow', to='applications.Backend'),
        ),
        migrations.AddField(
            model_name='frontend',
            name='error_template',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='system.ErrorTemplate'),
        ),
        migrations.AddField(
            model_name='frontend',
            name='headers',
            field=djongo.models.fields.ArrayReferenceField(help_text='Header rules', null=True, on_delete=django.db.models.deletion.CASCADE, to='toolkit.Header'),
        ),
        migrations.AddField(
            model_name='frontend',
            name='impcap_darwin_dns_filter',
            field=models.ForeignKey(help_text='Darwin prediction filter to use on DNS queries captured by Impcap', null=True, on_delete=django.db.models.deletion.SET_NULL, to='darwin.FilterPolicy', verbose_name='Darwin DGA filter to use on Impcap DNS queries'),
        ),
        migrations.AddField(
            model_name='frontend',
            name='impcap_intf',
            field=models.ForeignKey(help_text='Interface used by impcap for trafic listening', on_delete=django.db.models.deletion.PROTECT, to='system.NetworkInterfaceCard', verbose_name='Listening interface'),
        ),
        migrations.AddField(
            model_name='frontend',
            name='log_forwarders',
            field=djongo.models.fields.ArrayReferenceField(help_text='Log forwarders used in log_condition', null=True, on_delete=djongo.models.fields.ArrayReferenceField._on_delete, to='applications.LogOM'),
        ),
        migrations.AddField(
            model_name='frontend',
            name='logging_geoip_database',
            field=models.ForeignKey(default=None, help_text='MMDB database used by rsyslog to get Geoip location of an IPv4', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='frontend_geoip', to='gui.Feed'),
        ),
        migrations.AddField(
            model_name='frontend',
            name='logging_reputation_database_v4',
            field=models.ForeignKey(default=None, help_text='MMDB database used by rsyslog to get reputation tags for IPv4', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='frontend_reputation_v4', to='gui.Feed'),
        ),
        migrations.AddField(
            model_name='frontend',
            name='logging_reputation_database_v6',
            field=models.ForeignKey(default=None, help_text='MMDB database used by rsyslog to get reputation tags for IPv6', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='frontend_reputation_v6', to='gui.Feed'),
        ),
        migrations.AddField(
            model_name='frontend',
            name='reputation_ctxs',
            field=models.ManyToManyField(through='services.FrontendReputationContext', to='applications.ReputationContext'),
        ),
        migrations.AddField(
            model_name='blacklistwhitelist',
            name='frontend',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='services.Frontend'),
        ),
        migrations.AlterUniqueTogether(
            name='listener',
            unique_together={('network_address', 'port')},
        ),
    ]
